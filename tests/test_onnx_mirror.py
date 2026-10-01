# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

loader = importlib.util.spec_from_file_location(
    "onnx_mirror", Path(__file__).resolve().parents[1] / "dependencies/onnxruntime-mirror.py")
mirror = importlib.util.module_from_spec(loader)
loader.loader.exec_module(mirror)


class MirrorTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source, self.archives = self.root / "source", self.root / "archives"
        (self.source / "cmake").mkdir(parents=True)
        self.archives.mkdir()
        self.manifest = self.root / "manifest.json"
        self.info = {"url": "https://github.com/example/vendor/archive/v1.zip", "archive": "vendor.zip",
                     "sha1": hashlib.sha1(b"fixture").hexdigest(),
                     "sha256": hashlib.sha256(b"fixture").hexdigest()}
        (self.archives / "vendor.zip").write_bytes(b"fixture")
        self.write_inputs()

    def write_inputs(self):
        (self.source / "cmake/deps.txt").write_text(
            "# upstream pins\nvendor;" + self.info["url"] + ";" + self.info["sha1"] + "\n")
        self.manifest.write_text(json.dumps({"vendor": self.info}))

    def run_mirror(self):
        mirror.materialize(self.source, self.manifest, self.archives)

    def test_mirror_matches_upstream_lookup_path(self):
        self.run_mirror()
        self.assertEqual((self.source / "mirror/github.com/example/vendor/archive/v1.zip").read_bytes(), b"fixture")

    def test_tampered_component_leaves_no_mirror(self):
        (self.archives / "vendor.zip").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "checksum"):
            self.run_mirror()
        self.assertFalse((self.source / "mirror").exists())

    def test_manifest_must_agree_with_upstream(self):
        self.info["sha1"] = "0" * 40
        self.manifest.write_text(json.dumps({"vendor": self.info}))
        with self.assertRaisesRegex(ValueError, "source pin"):
            self.run_mirror()

    def test_escaping_urls_and_archive_names_are_rejected(self):
        for field, value in [("url", "https://github.com/../../escape.zip"), ("archive", "../secret")]:
            with self.subTest(field=field):
                original = self.info[field]
                self.info[field] = value
                self.write_inputs()
                with self.assertRaisesRegex(ValueError, "Unsafe"):
                    self.run_mirror()
                self.info[field] = original

    def test_symlink_archive_is_rejected(self):
        path = self.archives / "vendor.zip"
        path.unlink()
        path.symlink_to(self.manifest)
        with self.assertRaisesRegex(ValueError, "regular archive"):
            self.run_mirror()

    def test_existing_mirror_is_preserved(self):
        (self.source / "mirror").mkdir()
        (self.source / "mirror/keep").write_bytes(b"existing")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.run_mirror()
        self.assertEqual((self.source / "mirror/keep").read_bytes(), b"existing")

    def test_failed_write_leaves_no_mirror(self):
        with patch.object(mirror.os, "replace", side_effect=OSError("disk failure")):
            with self.assertRaisesRegex(OSError, "disk failure"):
                self.run_mirror()
        self.assertFalse((self.source / "mirror").exists())
