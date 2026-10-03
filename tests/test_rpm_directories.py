# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
import importlib.util
from pathlib import Path
import subprocess
import shlex
import tempfile
import unittest
from unittest.mock import patch

loader = importlib.util.spec_from_file_location(
    'rpm_directories', Path(__file__).resolve().parents[1] / 'tools/check-rpm-directories.py')
directories = importlib.util.module_from_spec(loader)
loader.loader.exec_module(directories)


class DirectoryOwnershipTest(unittest.TestCase):
    def test_kotlin_license_parent_regression(self):
        installed = {'/usr', '/usr/share', '/usr/share/doc', '/usr/share/doc/packages'}
        doc = '/usr/share/doc/packages/qore-jni-kotlin'
        package = {doc + '/upstream-licenses', doc + '/upstream-licenses/LICENSE'}
        self.assertEqual(directories.missing_parents(installed, {'kotlin': package}), {'kotlin': [doc]})
        self.assertEqual(directories.missing_parents(installed, {'kotlin': package | {doc}}), {'kotlin': []})

    def test_checks_all_intermediate_ancestors(self):
        self.assertEqual(directories.missing_parents({'/usr'}, {'p': {'/usr/share/qore/data/file'}}),
                         {'p': ['/usr/share', '/usr/share/qore', '/usr/share/qore/data']})

    def test_sibling_ownership_and_installed_symlinks(self):
        self.assertEqual(directories.missing_parents({'/lib64'}, {
            'runtime': {'/lib64/qore', '/lib64/qore/native.qmod'},
            'sdk': {'/lib64/qore/metadata'}}), {'runtime': [], 'sdk': []})

    def test_root_and_empty_payload(self):
        self.assertEqual(directories.missing_parents(set(), {'empty': set(), 'root': {'/bin'}}),
                         {'empty': [], 'root': []})

    def test_inventory_spaces_duplicates_and_bad_paths(self):
        filenames = ['/usr/share/license with spaces', "/usr/share/author's license", '/usr/share/line\nbreak']
        self.assertEqual(directories.paths('\n'.join(shlex.quote(name) for name in filenames + filenames)),
                         set(filenames))
        for value in ['relative', '/usr/../etc', '/usr//share', '/usr/./share', '//usr', '', '/usr/\0bad']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                directories.paths(shlex.quote(value))
        with self.assertRaises(ValueError):
            directories.paths("'unterminated")

    def test_real_package_paths_are_passed_without_shell(self):
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / 'a package.rpm'
            package.touch()
            with patch.object(directories.subprocess, 'check_output', side_effect=['/usr\n', '/usr/file\n']) as query:
                self.assertEqual(directories.check([package]), {str(package): []})
                self.assertEqual(query.call_args.args[0][-2:], ['--', str(package)])

    def test_query_failure_is_not_accepted(self):
        with patch.object(directories.subprocess, 'check_output', side_effect=subprocess.CalledProcessError(1, 'rpm')):
            with self.assertRaises(subprocess.CalledProcessError):
                directories.check(['bad.rpm'])

    def test_source_and_empty_package_sets_rejected(self):
        with patch.object(directories.subprocess, 'check_output', return_value=''):
            with self.assertRaises(ValueError):
                directories.check([])
            with tempfile.TemporaryDirectory() as tmp:
                for suffix in ['src.rpm', 'nosrc.rpm', 'tar.xz']:
                    source = Path(tmp) / ('package.' + suffix)
                    source.touch()
                    with self.subTest(suffix=suffix), self.assertRaises(ValueError):
                        directories.check([source])


if __name__ == '__main__':
    unittest.main()
