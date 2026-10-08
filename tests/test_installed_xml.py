# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Check archive isolation, failure cleanup, and installed XML test selection."""
import copy
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import test_installed_qualification as fixtures

module = fixtures.module
xml = module.installed_xml


class InstalledXmlTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.archive = self.root / 'source.tar'
        self.destination = self.root / 'fixtures'
        self.files = {'test/basic.qtest': b'%modern\n', 'docs/example.tmpl': b'example',
                      'rpm/run-tests.py': b'print(42)\n', 'debian/tests/compiler': b'#!/bin/sh\n'}

    def make_archive(self, extra=(), missing=()):
        with tarfile.open(self.archive, 'w') as archive:
            for path, data in self.files.items():
                if path in missing:
                    continue
                entry = tarfile.TarInfo(xml.ARCHIVE_ROOT + '/' + path)
                entry.size = len(data)
                entry.mode = 0o4666 if path.startswith('docs/') else 0o4777
                entry.uid = 12345
                archive.addfile(entry, io.BytesIO(data))
            for entry in extra:
                archive.addfile(entry, io.BytesIO(b'x' * entry.size))

    def extract(self):
        with patch.object(xml, 'FIXTURES', frozenset(self.files)):
            return xml.extract_fixtures(self.archive, self.destination)

    def test_regular_fixtures_only_with_safe_modes_and_full_inventory(self):
        extras = []
        for path in ('qlib/Fake.qm', 'src/module.cpp', 'build/xml-api-1.qmod'):
            entry = tarfile.TarInfo(xml.ARCHIVE_ROOT + '/' + path)
            entry.size = 1
            extras.append(entry)
        self.make_archive(extras)
        result = self.extract()
        self.assertEqual(result, {'files': 4, 'bytes': sum(map(len, self.files.values())), 'suites': 1})
        self.assertEqual({str(p.relative_to(self.destination)) for p in self.destination.rglob('*')
                          if p.is_file()}, set(self.files))
        for path, data in self.files.items():
            output = self.destination / path
            self.assertEqual(output.read_bytes(), data)
            self.assertEqual(output.stat().st_mode & 0o7777, 0o644 if path.startswith('docs/') else 0o755)
        self.assertFalse((self.destination / 'qlib').exists())

    def test_missing_and_unreviewed_fixtures_rejected_before_extraction(self):
        for missing in self.files:
            self.make_archive(missing=(missing,))
            with self.subTest(missing=missing), self.assertRaisesRegex(ValueError, 'Incomplete'):
                self.extract()
            self.assertFalse(self.destination.exists())
        entry = tarfile.TarInfo(xml.ARCHIVE_ROOT + '/test/new.qtest')
        self.make_archive([entry])
        with self.assertRaisesRegex(ValueError, 'Unreviewed'):
            self.extract()
        self.assertFalse(self.destination.exists())

    def test_paths_and_duplicate_members_rejected(self):
        for name in ('', '.', '/tmp/escape', '../escape', xml.ARCHIVE_ROOT + '/../escape',
                     xml.ARCHIVE_ROOT + '/test//double', 'wrong-root/test/file',
                     xml.ARCHIVE_ROOT + '/test/./dot', xml.ARCHIVE_ROOT + '/test/back\\slash',
                     xml.ARCHIVE_ROOT + '/test/basic.qtest'):
            self.make_archive([tarfile.TarInfo(name)])
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.extract()
            self.assertFalse(self.destination.exists())

    def test_links_devices_and_directories_cannot_replace_fixture_files(self):
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.CHRTYPE, tarfile.FIFOTYPE, tarfile.DIRTYPE):
            entry = tarfile.TarInfo(xml.ARCHIVE_ROOT + '/test/basic.qtest')
            entry.type = kind
            entry.linkname = '/etc/passwd'
            self.make_archive([entry], missing=('test/basic.qtest',))
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'regular files'):
                self.extract()
            self.assertFalse(self.destination.exists())

    def test_expansion_and_member_limits(self):
        self.make_archive()
        for field, limit in [('MAX_MEMBERS', 3), ('MAX_FIXTURE_BYTES', 1)]:
            with patch.object(xml, field, limit), self.subTest(field=field), self.assertRaises(ValueError):
                self.extract()
            self.assertFalse(self.destination.exists())

    def test_failed_copy_cleans_partial_fixture_tree(self):
        self.make_archive()
        before = set(self.root.iterdir())
        with patch.object(xml.shutil, 'copyfileobj', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(OSError, 'disk full'):
                self.extract()
        self.assertEqual(set(self.root.iterdir()), before)

    def test_existing_directory_and_dangling_link_are_never_overwritten(self):
        self.make_archive()
        self.destination.mkdir()
        sentinel = self.destination / 'keep'
        sentinel.write_text('preserve')
        with self.assertRaisesRegex(ValueError, 'must not exist'):
            self.extract()
        self.assertEqual(sentinel.read_text(), 'preserve')
        linked = self.root / 'dangling'
        linked.symlink_to(self.root / 'missing')
        with self.assertRaisesRegex(ValueError, 'must not exist'):
            xml.extract_fixtures(self.archive, linked)
        self.assertTrue(linked.is_symlink())

    def test_download_hash_mismatch_cannot_stage_files(self):
        def download(url, digest, destination):
            destination.write_bytes(b'corrupt')
        before = set(self.root.iterdir())
        with patch.object(xml, 'fetch_source', side_effect=download), patch.object(xml, 'extract_fixtures') as extract:
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                xml.stage(self.destination)
        extract.assert_not_called()
        self.assertEqual(set(self.root.iterdir()), before)

    def test_manifest_requires_reviewed_pin_and_all_runtime_dependencies(self):
        fixture = fixtures.InstalledQualificationTest('test_valid_native_manifest')
        fixture.setUp()
        fixture.add_modules()
        manifest = fixture.manifest
        manifest['modules'] = [entry for entry in manifest['modules'] if entry['name'] == 'xml']
        self.assertIs(module.validate(manifest), manifest)
        for name in ('qore-xml-module', 'qore-process-module', 'qore-uuid-module', 'litmus'):
            changed = copy.deepcopy(manifest)
            changed['packages'] = [p for p in changed['packages'] if p['name'] != name]
            with self.subTest(name=name), self.assertRaises(ValueError):
                module.validate(changed)
        for field, value in [('commit', 'a' * 40), ('fixtures', [{'path': 'qlib/Fake.qm'}])]:
            changed = copy.deepcopy(manifest)
            changed['modules'][0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'reviewed archive'):
                module.validate(changed)

    def test_runtime_and_sdk_commands_use_installed_artifacts(self):
        directory = Path('/tmp/XML fixtures ; quoted')
        runtime = module.module_commands('xml', 'runtime', directory)
        self.assertEqual(runtime, [('tests', ['python3', '-B', '-W', 'error',
                                             str(directory / 'rpm/run-tests.py'), '--installed'])])
        self.assertEqual(module.module_commands('xml', 'sdk', directory),
                         runtime + [('compiler', [str(directory / 'debian/tests/compiler')])])
        for family in ('fedora', 'suse', 'el'):
            self.assertEqual(module.module_dependencies('xml', 'runtime', family), [])
            self.assertEqual(module.module_dependencies('xml', 'sdk', family), [])


if __name__ == '__main__':
    unittest.main()
