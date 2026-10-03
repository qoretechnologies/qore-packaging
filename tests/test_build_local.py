# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

loader = importlib.util.spec_from_file_location("build_local", Path(__file__).resolve().parents[1] / "tools/build-local.py")
builder = importlib.util.module_from_spec(loader)
loader.loader.exec_module(builder)


class BundleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "probe.spec").write_bytes(b"recipe")
        self.manifest = {"schema": 1, "spec": "probe.spec", "source_date_epoch": 10,
                         "sources": {"probe.spec": hashlib.sha256(b"recipe").hexdigest()}}

    def verify(self):
        (self.root / "source-manifest.json").write_text(json.dumps(self.manifest))
        return builder.verify_bundle(self.root)

    def test_valid_bundle_and_tamper(self):
        self.assertEqual(self.verify(), self.manifest)
        (self.root / "probe.spec").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "mismatch"):
            self.verify()

    def test_manifest_cannot_escape_source_directory(self):
        self.manifest["sources"]["../secret"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "basenames"):
            self.verify()

    def test_unchecked_recipe_is_rejected(self):
        self.manifest["spec"] = "other.spec"
        with self.assertRaisesRegex(ValueError, "checksum is missing"):
            self.verify()

    def test_symlink_source_is_rejected(self):
        (self.root / "probe.spec").rename(self.root / "real.spec")
        (self.root / "probe.spec").symlink_to("real.spec")
        with self.assertRaisesRegex(ValueError, "regular files"):
            self.verify()

    def test_invalid_bundle_cannot_start_container(self):
        self.manifest["source_date_epoch"] = -1
        (self.root / "source-manifest.json").write_text(json.dumps(self.manifest))
        with patch.object(builder.subprocess, "check_output", side_effect=AssertionError("container started")):
            with self.assertRaisesRegex(ValueError, "timestamp"):
                builder.build(self.root, "image", self.root / "output")

    def test_missing_declared_source_cannot_start_foreground_or_background_build(self):
        recipe = b"Source1: vendor.tar.xz\n"
        (self.root / "probe.spec").write_bytes(recipe)
        self.manifest["sources"]["probe.spec"] = hashlib.sha256(recipe).hexdigest()
        (self.root / "source-manifest.json").write_text(json.dumps(self.manifest))
        with patch.object(builder.subprocess, "check_output", side_effect=AssertionError("engine called")), \
                patch.object(builder.os, "posix_spawn", side_effect=AssertionError("driver started")):
            for start in (builder.build, builder.launch_background):
                with self.subTest(start=start.__name__), self.assertRaisesRegex(ValueError, "missing.*vendor.tar"):
                    start(self.root, "image", self.root / "output")
        self.assertFalse((self.root / "output").exists())

    def test_container_isolation_and_recorded_success_or_failure(self):
        self.verify()
        image_id = "sha256:" + "a" * 64
        for status in (0, 1):
            with self.subTest(status=status):
                output = self.root / str(status)

                def run(command, **kwargs):
                    self.assertEqual(command[:7], ["docker", "run", "--rm", "--init", "--network", "none",
                                                   "--hostname"])
                    self.assertIn(image_id, command)
                    self.assertEqual(command[command.index("--user") + 1], f"{os.getuid()}:{os.getgid()}")
                    self.assertIn(str(self.root) + ":/sources:ro", command)
                    kwargs["stdout"].write("build log\n")
                    if status == 0:
                        (output / "probe.rpm").write_bytes(b"artifact")
                    return subprocess.CompletedProcess(command, status)

                with patch.object(builder.subprocess, "check_output", return_value=json.dumps([{"Id": image_id}])), \
                     patch.object(builder.subprocess, "run", side_effect=run):
                    self.assertEqual(status, builder.build(self.root, "mutable-tag", output))
                record = json.loads((output / "build.json").read_text())
                self.assertEqual(status, record["exit_code"])
                expected = {"probe.rpm": hashlib.sha256(b"artifact").hexdigest()} if status == 0 else {}
                self.assertEqual(expected, record["artifacts"])
                self.assertEqual("build log\n", (output / "build.log").read_text())

    def test_tmpfs_capacity_validation_precedes_engine_and_filesystem_changes(self):
        self.verify()
        for size in (0, -1, 127, 32769, True, 1024.5, "1024m,exec"):
            for start in (builder.build, builder.launch_background):
                with self.subTest(size=size, start=start.__name__), \
                        patch.object(builder.subprocess, "check_output") as engine, \
                        patch.object(builder.os, "posix_spawn") as spawn:
                    with self.assertRaisesRegex(ValueError, "128..32768 MiB"):
                        start(self.root, "image", self.root / "invalid", tmpfs_mib=size)
                    engine.assert_not_called()
                    spawn.assert_not_called()
                    self.assertFalse((self.root / "invalid").exists())

    def test_tmpfs_is_optional_and_recorded_with_exact_bounded_capacity(self):
        self.verify()
        for size in (None, 128, 4096, 32768):
            output = self.root / str(size)
            with self.subTest(size=size), \
                    patch.object(builder.subprocess, "check_output",
                                 return_value=json.dumps([{"Id": "sha256:" + "a" * 64}])), \
                    patch.object(builder.subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
                self.assertEqual(builder.build(self.root, "image", output, tmpfs_mib=size), 0)
                command = run.call_args.args[0]
                self.assertEqual(command.count("--tmpfs"), int(size is not None))
                if size is not None:
                    self.assertEqual(command[command.index("--tmpfs") + 1],
                                     f"/tmp:rw,exec,nosuid,nodev,size={size}m,mode=1777")
                record = json.loads((output / "build.json").read_text())
                self.assertEqual(record["tmpfs_mib"], size)
                self.assertEqual(record["command"], command)

    def test_background_driver_pins_image_and_detaches_all_terminal_streams(self):
        self.verify()
        image_id = "sha256:" + "a" * 64
        output = self.root / "background"
        with patch.object(builder.subprocess, "check_output", return_value=json.dumps([{"Id": image_id}])), \
             patch.object(builder.os, "posix_spawn", return_value=12345) as start:
            result = builder.launch_background(self.root, "mutable-tag", output, source_only=True,
                                               internal_interface=True, tmpfs_mib=4096)
            command = start.call_args.args[1]
            options = start.call_args.kwargs
            self.assertIn(image_id, command)
            self.assertNotIn("mutable-tag", command)
            self.assertNotIn("--background", command)
            self.assertIn("--source-only", command)
            self.assertIn("--internal-interface", command)
            self.assertEqual(command[command.index("--tmpfs-mib") + 1], "4096")
            self.assertTrue(options["setsid"])
            actions = options["file_actions"]
            self.assertEqual(actions[0], (os.POSIX_SPAWN_OPEN, 0, os.devnull, os.O_RDONLY, 0))
            self.assertEqual(actions[1][::2], (os.POSIX_SPAWN_DUP2, 1))
            self.assertEqual(actions[2], (os.POSIX_SPAWN_DUP2, actions[1][1], 2))
            self.assertEqual(actions[3], (os.POSIX_SPAWN_CLOSE, actions[1][1]))
            self.assertEqual(result["driver_log"], str(self.root / "background-driver.log"))
            self.assertEqual(result["pid"], 12345)
            self.assertNotIn("exit_code", result)
            with self.assertRaises(FileExistsError):
                builder.launch_background(self.root, "mutable-tag", output)
            self.assertEqual(start.call_count, 1)

    def test_background_driver_rejects_invalid_inputs_before_launch(self):
        self.verify()
        with patch.object(builder.os, "posix_spawn", side_effect=AssertionError("launched")):
            with self.assertRaisesRegex(ValueError, "build jobs"):
                builder.launch_background(self.root, "image", self.root / "output", jobs=0)
            with self.assertRaisesRegex(ValueError, "new build output"):
                builder.launch_background(self.root, "image", self.root)
            (self.root / "probe.spec").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "checksum"):
                builder.launch_background(self.root, "image", self.root / "output")

    def test_real_background_driver_records_completion_without_terminal(self):
        self.verify()
        image_id = "sha256:" + "a" * 64
        binary = self.root / "bin"
        binary.mkdir()
        engine = binary / "docker"
        engine.write_text('''#!/usr/bin/env python3
import json,pathlib,sys
args=sys.argv[1:]
if args[:2] == ["image", "inspect"]:
    print(json.dumps([{"Id": "sha256:" + "a" * 64}]))
elif args[0] == "run":
    output=next(value[:-6] for value in args if value.endswith(":/work"))
    pathlib.Path(output, "probe.rpm").write_bytes(b"artifact")
    print("offline build completed")
else:
    raise SystemExit(2)
''')
        engine.chmod(0o755)
        output = self.root / "detached"
        with patch.dict(os.environ, PATH=str(binary) + os.pathsep + os.environ["PATH"]):
            result = builder.launch_background(self.root, image_id, output)
        # Reap our direct child using its completion event; no timed polling.
        _, status = os.waitpid(result["pid"], 0)
        self.assertEqual(os.waitstatus_to_exitcode(status), 0)
        record = json.loads((output / "build.json").read_text())
        self.assertEqual(record["exit_code"], 0)
        self.assertEqual(record["image"], image_id)
        self.assertEqual(record["artifacts"], {"probe.rpm": hashlib.sha256(b"artifact").hexdigest()})
        self.assertEqual((output / "build.log").read_text(), "offline build completed\n")
        self.assertEqual(Path(result["driver_log"]).read_text(), "")


class IsolatedNetworkTest(unittest.TestCase):
    def setUp(self):
        self.network_id = "b" * 64
        self.name = "qore-rpm-isolated-test"
        self.info = {"Id": self.network_id, "Name": self.name, "Driver": "bridge", "Internal": True,
                     "Containers": {}, "Options": {
                         "com.docker.network.bridge.gateway_mode_ipv4": "isolated",
                         "com.docker.network.bridge.gateway_mode_ipv6": "isolated"}}
        self.uuid = patch.object(builder.uuid, "uuid4", return_value=SimpleNamespace(hex="test"))
        self.uuid.start()
        self.addCleanup(self.uuid.stop)

    def test_internal_network_is_removed_after_success_and_build_exception(self):
        for failure in (False, True):
            with self.subTest(failure=failure), \
                    patch.object(builder.subprocess, "check_output",
                                 side_effect=[self.network_id, json.dumps([self.info])]) as query, \
                    patch.object(builder.subprocess, "run") as remove:
                try:
                    with builder.build_network("docker", True) as (network, info):
                        self.assertEqual(network, self.network_id)
                        self.assertEqual(info, self.info)
                        self.assertFalse(remove.called)
                        if failure:
                            raise RuntimeError("build failed")
                except RuntimeError as error:
                    self.assertTrue(failure)
                    self.assertEqual(str(error), "build failed")
                self.assertIn("--internal", query.call_args_list[0].args[0])
                self.assertIn("com.docker.network.bridge.gateway_mode_ipv4=isolated",
                              query.call_args_list[0].args[0])
                remove.assert_called_once_with(["docker", "network", "rm", self.name], check=True,
                                               stdout=subprocess.DEVNULL)

    def test_invalid_network_is_rejected_and_removed_before_container_start(self):
        for key, value in [("Internal", False), ("Driver", "host"), ("Id", "c" * 64),
                           ("Name", "other"), ("Containers", {"unexpected": {}}), ("Options", {})]:
            info = {**self.info, key: value}
            with self.subTest(key=key), \
                    patch.object(builder.subprocess, "check_output",
                                 side_effect=[self.network_id, json.dumps([info])]), \
                    patch.object(builder.subprocess, "run") as remove:
                with self.assertRaisesRegex(ValueError, "empty isolated internal bridge"):
                    with builder.build_network("docker", True):
                        self.fail("unsafe network was accepted")
                remove.assert_called_once()

    def test_malformed_create_response_and_failed_inspect_are_cleaned_up(self):
        for responses in [["not-a-network-id"],
                          [self.network_id, subprocess.CalledProcessError(1, ["inspect"])]]:
            with self.subTest(responses=responses), \
                    patch.object(builder.subprocess, "check_output", side_effect=responses), \
                    patch.object(builder.subprocess, "run") as remove:
                with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                    with builder.build_network("docker", True):
                        self.fail("failed network setup was accepted")
                remove.assert_called_once()

    def test_default_mode_needs_no_network_resource(self):
        with patch.object(builder.subprocess, "check_output", side_effect=AssertionError("engine called")), \
                patch.object(builder.subprocess, "run", side_effect=AssertionError("engine called")):
            with builder.build_network("docker") as (network, info):
                self.assertEqual(network, "none")
                self.assertIsNone(info)
            with self.assertRaisesRegex(ValueError, "requires Docker"):
                with builder.build_network("podman", True):
                    self.fail("unsupported engine accepted")

    def test_failed_creation_preserves_error_without_removing_other_networks(self):
        error = subprocess.CalledProcessError(1, ["create"])
        with patch.object(builder.subprocess, "check_output", side_effect=error), \
                patch.object(builder.subprocess, "run") as remove:
            with self.assertRaises(subprocess.CalledProcessError) as raised:
                with builder.build_network("docker", True):
                    self.fail("failed creation accepted")
            self.assertIs(raised.exception, error)
            remove.assert_not_called()
