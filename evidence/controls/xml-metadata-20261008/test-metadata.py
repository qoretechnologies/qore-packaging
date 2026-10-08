#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Check metadata deduplication through the actual expanded RPM install command."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
METADATA = None


def consolidate(directory):
    expanded = subprocess.check_output(['rpmspec', '-P', str(ROOT / 'qore-xml-module.spec')], text=True)
    marker = '# Deduplicate immutable compiler metadata without changing its contents.\n'
    if expanded.count(marker) != 1:
        raise AssertionError('Expected the reviewed metadata installation stanza')
    command = expanded.split(marker, 1)[1].splitlines()[0]
    arguments = shlex.split(command)
    if arguments[:3] != ['hardlink', '-t', '-O'] or len(arguments) != 4:
        raise AssertionError('Unexpected metadata install command: ' + command)
    command = command.replace(arguments[3], shlex.quote(str(directory)))
    result = subprocess.run(['sh', '-eu', '-c', command], cwd=directory.parent,
                            check=True, capture_output=True)
    if result.stderr:
        raise AssertionError(result.stderr.decode())


class MetadataPayloadTest(unittest.TestCase):
    def test_hardlink_dependency_is_retained_without_documentation(self):
        for options in ([], ['--without', 'tests']):
            requires = subprocess.check_output(
                ['rpmspec', '-q', '--buildrequires', '--without', 'docs', *options,
                 str(ROOT / 'qore-xml-module.spec')], text=True).splitlines()
            with self.subTest(options=options):
                self.assertEqual(len({'util-linux', 'util-linux-core'} & set(requires)), 1)
                self.assertNotIn('doxygen', requires)

    def test_complete_real_module_metadata(self):
        modules = json.loads((ROOT / 'debian/tests/modules.json').read_text())
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'metadata'
            shutil.copytree(METADATA, directory)
            self.assertEqual({p.name for p in directory.glob('*.qm.meta.json')},
                             {name + '.qm.meta.json' for name in modules})
            before = {p.name: (p.read_bytes(), stat.S_IMODE(p.stat().st_mode)) for p in directory.iterdir()}
            groups = defaultdict(list)
            for name, (data, mode) in before.items():
                json.loads(data)
                groups[(data, mode)].append(name)
            self.assertIn({'SoapClientIo.qm.meta.json', 'WebContentUtil.qm.meta.json',
                           'WebDavClientIo.qm.meta.json'}, [set(names) for names in groups.values()])
            consolidate(directory)
            for names in groups.values():
                self.assertEqual(len({(directory / name).stat().st_ino for name in names}), 1)
                for name in names:
                    path = directory / name
                    self.assertEqual((path.read_bytes(), stat.S_IMODE(path.stat().st_mode)), before[name])

    def test_different_content_and_modes_remain_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name, data, mode in [('first.json', b'{"a":1}', 0o644),
                                     ('equal.json', b'{"a":1}', 0o644),
                                     ('different.json', b'{"a":2}', 0o644),
                                     ('private.json', b'{"a":1}', 0o600)]:
                path = directory / name
                path.write_bytes(data)
                path.chmod(mode)
            consolidate(directory)
            self.assertTrue((directory / 'first.json').samefile(directory / 'equal.json'))
            for name in ('different.json', 'private.json'):
                self.assertFalse((directory / 'first.json').samefile(directory / name))
            self.assertEqual((directory / 'different.json').read_bytes(), b'{"a":2}')
            self.assertEqual(stat.S_IMODE((directory / 'private.json').stat().st_mode), 0o600)

    def test_paths_with_spaces_and_shell_metacharacters(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'metadata ; $(touch UNEXPECTED)'
            directory.mkdir()
            for name in ('a with space.json', 'b;quotes.json'):
                (directory / name).write_bytes(b'{"value":42}')
            consolidate(directory)
            self.assertTrue((directory / 'a with space.json').samefile(directory / 'b;quotes.json'))
            self.assertFalse((Path(temporary) / 'UNEXPECTED').exists())

    def test_only_the_metadata_directory_is_modified(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / 'metadata'
            directory.mkdir()
            outside = root / 'outside.json'
            outside.write_bytes(b'{}')
            original = outside.stat()
            for name in ('first.json', 'second.json'):
                (directory / name).write_bytes(b'{}')
            (directory / 'external-link').symlink_to(outside)
            consolidate(directory)
            self.assertTrue((directory / 'external-link').is_symlink())
            self.assertEqual((outside.read_bytes(), outside.stat().st_ino, outside.stat().st_nlink),
                             (b'{}', original.st_ino, original.st_nlink))
            self.assertFalse((directory / 'first.json').samefile(outside))

    def test_empty_directory_succeeds(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            consolidate(directory)
            self.assertEqual(list(directory.iterdir()), [])

    def test_idempotence_and_oldest_timestamp(self):
        import os
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for name, stamp in [('older.json', 1000), ('newer.json', 2000)]:
                path = directory / name
                path.write_bytes(b'{"immutable":true}')
                os.utime(path, (stamp, stamp))
            consolidate(directory)
            inode = (directory / 'older.json').stat().st_ino
            consolidate(directory)
            for path in directory.iterdir():
                self.assertEqual(path.read_bytes(), b'{"immutable":true}')
                self.assertEqual(path.stat().st_mtime, 1000)
                self.assertEqual(path.stat().st_ino, inode)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata-dir', type=Path, required=True)
    args, rest = parser.parse_known_args()
    METADATA = args.metadata_dir.resolve(strict=True)
    unittest.main(argv=[__file__, *rest])
