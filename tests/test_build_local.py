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
