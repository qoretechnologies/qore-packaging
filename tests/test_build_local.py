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

    def test_background_driver_pins_image_and_detaches_all_terminal_streams(self):
        self.verify()
        image_id = "sha256:" + "a" * 64
        output = self.root / "background"
        with patch.object(builder.subprocess, "check_output", return_value=json.dumps([{"Id": image_id}])), \
             patch.object(builder.os, "posix_spawn", return_value=12345) as start:
            result = builder.launch_background(self.root, "mutable-tag", output, source_only=True)
            command = start.call_args.args[1]
            options = start.call_args.kwargs
            self.assertIn(image_id, command)
            self.assertNotIn("mutable-tag", command)
            self.assertNotIn("--background", command)
            self.assertIn("--source-only", command)
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
