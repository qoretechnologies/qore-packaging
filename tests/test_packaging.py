# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
import importlib.util
import json
import io
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("packaging_tools", ROOT / "tools/packaging.py")
packaging = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packaging)


class CatalogTests(unittest.TestCase):
    def test_inventory_and_order(self):
        catalog = json.loads((ROOT / "catalog.json").read_text())["packages"]
        self.assertEqual(len(catalog), 38)
        order = packaging.build_order(catalog)
        for name, info in catalog.items():
            for prerequisite in info["build_after"]:
                self.assertLess(order.index(prerequisite), order.index(name))
            self.assertRegex(info["commit"], r"^[0-9a-f]{40}$")

    def test_missing_prerequisite(self):
        with self.assertRaisesRegex(ValueError, "Unknown prerequisites"):
            packaging.build_order({"a": {"build_after": ["missing"]}})

    def test_cycle(self):
        with self.assertRaisesRegex(ValueError, "cycle"):
            packaging.build_order({"a": {"build_after": ["b"]}, "b": {"build_after": ["a"]}})

    def test_target_images_are_pinned_and_unqualified(self):
        for path in (ROOT / "targets").glob("*.json"):
            target = json.loads(path.read_text())
            self.assertRegex(target["image"], r"@sha256:[0-9a-f]{64}$")
            self.assertEqual(target["qualified"], [])


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Packaging Tests")
        (self.repo / "source.txt").write_text("committed\n")
        (self.repo / "excluded").mkdir()
        (self.repo / "excluded/data").write_text("excluded\n")
        (self.repo / "link").symlink_to("source.txt")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")

    def git(self, *args):
        return packaging.git(self.repo, *args)

    def prepare(self, output="result", **overrides):
        kwargs = dict(repo=self.repo, ref="HEAD", name="qore-test-module",
                      version="1.0.0~git20261001.1", output=self.root / output)
        kwargs.update(overrides)
        return packaging.prepare_source(**kwargs)

    def test_clean_reproducible_archive(self):
        (self.repo / "source.txt").write_text("uncommitted\n")
        (self.repo / "untracked").write_text("secret\n")
        first = self.prepare("first", exclusions=["excluded"])
        second = self.prepare("second", exclusions=["excluded"])
        self.assertEqual(first, second)
        filename = next(iter(first["sources"]))
        self.assertEqual((self.root / "first" / filename).read_bytes(),
                         (self.root / "second" / filename).read_bytes())
        with tarfile.open(self.root / "first" / filename) as archive:
            members = archive.getmembers()
            self.assertEqual(len(members), 2)
            self.assertEqual(archive.extractfile(members[1]).read(), b"committed\n")
            self.assertTrue(members[0].issym())
            for member in members:
                self.assertEqual(member.uid, 0)
                self.assertEqual(member.mtime, first["source_date_epoch"])

    def test_invalid_version_and_name(self):
        for kwargs in [{"version": "../bad"}, {"name": "../bad"}, {"version": "1.0-1"}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.prepare(**kwargs)
        self.assertFalse((self.root / "result").exists())

    def test_existing_destination_is_preserved(self):
        output = self.root / "result"
        output.mkdir()
        (output / "keep").write_text("untouched")
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertEqual((output / "keep").read_text(), "untouched")

    def test_invalid_commit_leaves_no_destination(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.prepare(ref="does-not-exist")
        self.assertFalse((self.root / "result").exists())

    def test_escaping_symlink_is_rejected(self):
        (self.repo / "escape").symlink_to("../outside")
        self.git("add", "escape")
        self.git("commit", "-qm", "bad symlink")
        with self.assertRaisesRegex(ValueError, "escapes"):
            self.prepare()
        self.assertFalse((self.root / "result").exists())

    def test_io_failure_leaves_no_destination(self):
        with patch.object(packaging.os, "replace", side_effect=OSError("injected")):
            with self.assertRaisesRegex(OSError, "injected"):
                self.prepare()
        self.assertFalse((self.root / "result").exists())
        self.assertEqual(list(self.root.glob(".qore-source-*")), [])

    def test_checksum_verification(self):
        path = self.repo / "source.txt"
        digest = packaging.hashlib.sha256(path.read_bytes()).hexdigest()
        packaging.verify_download(path, digest)
        with self.assertRaisesRegex(ValueError, "mismatch"):
            packaging.verify_download(path, "0" * 64)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            packaging.verify_download(path, "wrong")

    def test_candidate_overlay_is_recorded_and_limited_to_packaging(self):
        overlay = self.root / "overlay"
        (overlay / "rpm").mkdir(parents=True)
        (overlay / "rpm/check.py").write_text("check\n")
        (overlay / "source.txt").write_text("must not be used\n")
        manifest = self.prepare(packaging_overlay=overlay)
        self.assertTrue(manifest["candidate"])
        self.assertEqual(list(manifest["packaging_overlay"]), ["rpm/check.py"])
        with tarfile.open(self.root / "result" / next(iter(manifest["sources"]))) as archive:
            prefix = "qore-test-module-1.0.0~git20261001.1/"
            self.assertEqual(archive.extractfile(prefix + "source.txt").read(), b"committed\n")
            self.assertEqual(archive.extractfile(prefix + "rpm/check.py").read(), b"check\n")

    def test_candidate_symlink_is_rejected(self):
        overlay = self.root / "overlay"
        overlay.mkdir()
        (overlay / "bad.spec").symlink_to("/etc/passwd")
        with self.assertRaisesRegex(ValueError, "regular files"):
            self.prepare(packaging_overlay=overlay)

    def test_snapshot_spec_and_archive_agree(self):
        recipe = self.repo / "qore-test-module.spec"
        recipe.write_text("Name: qore-test-module\nVersion: 1.0.0\nRelease: 1\n")
        self.git("add", recipe.name)
        self.git("commit", "-qm", "recipe")
        manifest = self.prepare(spec_path=recipe.name)
        path = self.root / "result" / manifest["spec"]
        self.assertIn("Version: 1.0.0~git20261001.1\n", path.read_text())
        packaging.verify_download(path, manifest["sources"][path.name])

    def test_mismatching_recipe_is_rejected(self):
        recipe = self.repo / "bad.spec"
        recipe.write_text("Name: another-name\nVersion: 1.0.0\n")
        self.git("add", recipe.name)
        self.git("commit", "-qm", "invalid recipe")
        with self.assertRaisesRegex(ValueError, "name does not match"):
            self.prepare(spec_path=recipe.name)


class VendorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def archive(self, names):
        path = self.root / "vendor.tar"
        with tarfile.open(path, "w") as archive:
            for name in names:
                item = tarfile.TarInfo(name)
                item.size, item.mtime = 4, 123
                archive.addfile(item, io.BytesIO(b"data"))
        return path, packaging.hashlib.sha256(path.read_bytes()).hexdigest()

    def test_repack_retains_licenses_and_excludes_fixtures_reproducibly(self):
        source, digest = self.archive(["lib-1/LICENSE", "lib-1/src/a.c", "lib-1/test/a.c"])
        first = self.root / "first.tar.xz"
        second = self.root / "second.tar.xz"
        one = packaging.repack_component(source, digest, "lib-1", 456, first, exclusions=["test"])
        two = packaging.repack_component(source, digest, "lib-1", 456, second, retained=["LICENSE", "src"])
        self.assertEqual(one, two)
        with tarfile.open(first) as archive:
            self.assertEqual(archive.getnames(), ["lib-1/LICENSE", "lib-1/src/a.c"])
            self.assertTrue(all(m.mtime == 456 for m in archive.getmembers()))

    def test_repack_rejects_escaping_paths_before_writing(self):
        source, digest = self.archive(["lib-1/../../outside"])
        output = self.root / "bad.tar.xz"
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            packaging.repack_component(source, digest, "lib-1", 1, output)
        self.assertFalse(output.exists())

    def test_failed_download_never_enters_cache(self):
        output = self.root / "download"
        with patch.object(packaging.urllib.request, "urlopen", return_value=io.BytesIO(b"bad")):
            with self.assertRaisesRegex(ValueError, "checksum"):
                packaging.fetch_source("https://example.invalid/source", "0" * 64, output)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.root.iterdir()), [])

    def test_cached_download_is_verified_without_network(self):
        path = self.root / "download"
        path.write_bytes(b"source")
        digest = packaging.hashlib.sha256(b"source").hexdigest()
        with patch.object(packaging.urllib.request, "urlopen", side_effect=AssertionError("network")):
            self.assertEqual(packaging.fetch_source("https://example.invalid/source", digest, path), path)
            with self.assertRaisesRegex(ValueError, "mismatch"):
                packaging.fetch_source("https://example.invalid/source", "0" * 64, path)


if __name__ == "__main__":
    unittest.main()
