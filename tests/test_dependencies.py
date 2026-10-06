# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

loader = importlib.util.spec_from_file_location(
    "dependencies", Path(__file__).resolve().parents[1] / "tools/prepare-dependency.py")
dependencies = importlib.util.module_from_spec(loader)
loader.loader.exec_module(dependencies)


class DependencyTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo, self.cache = self.root / "repo", self.root / "cache"
        (self.repo / "dependencies").mkdir(parents=True)
        self.cache.mkdir()
        self.info = {"version": "1.0", "archive": "probe-1.0.tar.gz",
                     "url": "https://example.org/probe-1.0.tar.gz", "source_date_epoch": 100,
                     "sha256": hashlib.sha256(b"archive fixture").hexdigest(),
                     "extra_sources": ["fix.patch"]}
        self.write_config()
        (self.repo / "dependencies/probe.spec").write_text(
            "Name: probe\nVersion: 1.0\nSource0: %{name}-%{version}.tar.gz\nPatch0: fix.patch\n")
        (self.repo / "dependencies/fix.patch").write_bytes(b"patch fixture")
        (self.cache / "probe-1.0.tar.gz").write_bytes(b"archive fixture")

    def write_config(self):
        (self.repo / "dependencies/sources.json").write_text(json.dumps({"probe": self.info}))

    def prepare(self, **kwargs):
        return dependencies.prepare(self.repo, "probe", self.cache, self.root / "output", **kwargs)

    def test_candidate_records_every_input_and_cannot_be_mistaken_for_a_commit(self):
        result = self.prepare(candidate=True)
        self.assertTrue(result["candidate"])
        self.assertIsNone(result["commit"])
        self.assertEqual(set(result["sources"]), {"probe.spec", "probe-1.0.tar.gz", "fix.patch"})
        for name, digest in result["sources"].items():
            self.assertEqual(hashlib.sha256((self.root / "output" / name).read_bytes()).hexdigest(), digest)

    def test_generated_obs_changelog_is_pinned_without_changing_recipe(self):
        path = self.repo / 'dependencies/probe.spec'
        recipe = path.read_text() + ('%changelog\n* Tue Oct 06 2026 Test <test@example.invalid> - 1.0-1\n'
                                    '- Offline dependency package.\n')
        path.write_text(recipe)
        manifest = self.prepare(candidate=True)
        changes = (self.root / 'output/probe.changes').read_bytes()
        self.assertEqual(changes.decode(), dependencies.packaging.obs_changelog(recipe))
        self.assertEqual(manifest['sources']['probe.changes'], hashlib.sha256(changes).hexdigest())
        self.assertEqual((self.root / 'output/probe.spec').read_text(), recipe)
        self.assertEqual((self.root / 'output/probe-1.0.tar.gz').read_bytes(), b'archive fixture')

    def test_conflicting_obs_changelog_cannot_replace_declared_source(self):
        path = self.repo / 'dependencies/probe.spec'
        path.write_text(path.read_text() + '%changelog\n* Tue Oct 06 2026 Test\n- Note.\n')
        self.info['extra_sources'].append('probe.changes')
        self.write_config()
        (self.repo / 'dependencies/probe.changes').write_text('different input')
        with self.assertRaisesRegex(ValueError, 'changelog disagrees'):
            self.prepare(candidate=True)
        self.assertFalse((self.root / 'output').exists())
        self.assertEqual(list(self.root.glob('.dependency-*')), [])

    def test_matching_declared_obs_changelog_is_preserved(self):
        path = self.repo / 'dependencies/probe.spec'
        recipe = path.read_text() + '%changelog\n* Tue Oct 06 2026 Test\n- Note.\n'
        path.write_text(recipe)
        self.info['extra_sources'].append('probe.changes')
        self.write_config()
        changes = dependencies.packaging.obs_changelog(recipe)
        (self.repo / 'dependencies/probe.changes').write_text(changes)
        self.prepare(candidate=True)
        self.assertEqual((self.root / 'output/probe.changes').read_text(), changes)

    def test_committed_packaging_ignores_dirty_working_files(self):
        def git(*args):
            return subprocess.check_output(["git", "-C", str(self.repo), *args], stderr=subprocess.PIPE)
        git("init", "-q")
        git("add", "dependencies")
        git("-c", "user.name=Test", "-c", "user.email=test@example.org", "commit", "-qm", "fixture")
        commit = git("rev-parse", "HEAD").decode().strip()
        (self.repo / "dependencies/fix.patch").write_bytes(b"uncommitted")
        result = self.prepare(ref=commit)
        self.assertNotIn("candidate", result)
        self.assertEqual(result["commit"], commit)
        self.assertEqual((self.root / "output/fix.patch").read_bytes(), b"patch fixture")

    def test_invalid_archive_never_creates_output(self):
        (self.cache / "probe-1.0.tar.gz").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "checksum"):
            self.prepare(candidate=True)
        self.assertFalse((self.root / "output").exists())

    def test_unlisted_patch_never_creates_output(self):
        self.info["extra_sources"] = []
        self.write_config()
        with self.assertRaisesRegex(ValueError, "missing.*fix.patch"):
            self.prepare(candidate=True)
        self.assertFalse((self.root / "output").exists())
        self.assertEqual(list(self.root.glob(".dependency-*")), [])

    def test_every_vendor_component_is_pinned_and_verified(self):
        self.info["components"] = [{"archive": "vendor.zip", "url": "https://example.org/vendor.zip",
                                    "sha256": hashlib.sha256(b"vendor").hexdigest()}]
        self.write_config()
        vendor = self.cache / "vendor.zip"
        vendor.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "checksum"):
            self.prepare(candidate=True)
        self.assertFalse((self.root / "output").exists())
        vendor.write_bytes(b"vendor")
        manifest = self.prepare(candidate=True)
        self.assertEqual(manifest["components"], self.info["components"])
        self.assertEqual((self.root / "output/vendor.zip").read_bytes(), b"vendor")

    def test_component_cannot_replace_recipe(self):
        self.info["components"] = [{"archive": "probe.spec", "sha256": "0" * 64}]
        self.write_config()
        with self.assertRaisesRegex(ValueError, "unique safe"):
            self.prepare(candidate=True)

    def test_source_paths_cannot_escape_or_collide(self):
        for extra in [["../secret"], ["probe.spec"]]:
            with self.subTest(extra=extra):
                self.info["extra_sources"] = extra
                self.write_config()
                with self.assertRaisesRegex(ValueError, "unique safe"):
                    self.prepare(candidate=True)

    def test_symlink_packaging_is_rejected(self):
        path = self.repo / "dependencies/fix.patch"
        path.unlink()
        path.symlink_to("probe.spec")
        with self.assertRaisesRegex(ValueError, "regular files"):
            self.prepare(candidate=True)

    def test_mismatched_version_is_rejected(self):
        (self.repo / "dependencies/probe.spec").write_text("Name: probe\nVersion: 2.0\n")
        with self.assertRaisesRegex(ValueError, "disagree: Version"):
            self.prepare(candidate=True)

    def test_generated_pkgconfig_metadata_is_not_package_metadata(self):
        spec = self.repo / "dependencies/probe.spec"
        spec.write_text(spec.read_text() + "\n%install\ncat > probe.pc <<'PC'\n"
                        "Name: Embedded library\nVersion: %{version}\nSource: upstream\nPC\n")
        result = self.prepare(candidate=True)
        self.assertEqual(result["version"], "1.0")
        self.assertEqual((self.root / "output/probe.spec").read_text(), spec.read_text())

    def test_generated_version_cannot_supply_missing_package_version(self):
        spec = self.repo / "dependencies/probe.spec"
        spec.write_text("Name: probe\n%description\nExample:\nVersion: 1.0\n")
        with self.assertRaisesRegex(ValueError, "disagree: Version"):
            self.prepare(candidate=True)
        self.assertFalse((self.root / "output").exists())

    def test_failed_atomic_write_leaves_no_output(self):
        with patch.object(dependencies.os, "replace", side_effect=OSError("disk failure")):
            with self.assertRaisesRegex(OSError, "disk failure"):
                self.prepare(candidate=True)
        self.assertFalse((self.root / "output").exists())

    def test_existing_output_is_not_overwritten(self):
        (self.root / "output").mkdir()
        (self.root / "output/keep").write_bytes(b"existing")
        with self.assertRaisesRegex(ValueError, "must not exist"):
            self.prepare(candidate=True)
        self.assertEqual((self.root / "output/keep").read_bytes(), b"existing")

    def test_packaging_selection_must_be_explicit_and_unambiguous(self):
        for options in [{}, {"candidate": True, "ref": "HEAD"}]:
            with self.subTest(options=options), self.assertRaisesRegex(ValueError, "exactly one"):
                self.prepare(**options)
