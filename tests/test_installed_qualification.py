# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
loader = importlib.util.spec_from_file_location('qualify_installed', Path(__file__).resolve().parents[1] / 'tools/qualify-installed.py')
module = importlib.util.module_from_spec(loader)
loader.loader.exec_module(module)


class InstalledQualificationTest(unittest.TestCase):
    def setUp(self):
        self.manifest = {'schema': 1, 'family': 'fedora', 'arch': 'aarch64', 'core_commit': 'a' * 40,
                         'fixtures': [{'path': path, 'sha256': 'b' * 64, 'url': 'https://example.org/' + path}
                                      for path in sorted(module.FIXTURES)], 'packages': []}
        for name in ('qore', 'libqore', 'qore-stdlib', 'qore-devel', 'qore-rpm-macros', 'qore-misc-tools', 'qore-debug-tools'):
            self.manifest['packages'].append({'name': name, 'filename': name + '-3.0-1.aarch64.rpm',
                'url': 'https://example.org/' + name, 'sha256': 'c' * 64,
                'phase': 'runtime' if name in ('qore', 'libqore', 'qore-stdlib') else 'sdk'})

    def test_valid_native_manifest(self):
        self.assertEqual(module.validate(self.manifest), self.manifest)

    def test_wrong_architecture_rejected_before_mutation(self):
        with patch.object(module.platform, 'machine', return_value='x86_64'), patch.object(module.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'matching native runner'):
                module.qualify(self.manifest, 'not-created')
            run.assert_not_called()

    def test_rejects_unsafe_or_incomplete_inputs(self):
        variants = []
        for field, value in [('filename', '../bad.rpm'), ('filename', 'qore-1-1.src.rpm'),
                             ('filename', 'qore-1-1.x86_64.rpm'), ('name', '-bad'), ('phase', 'sdk'),
                             ('sha256', 'not-a-hash'), ('url', 'http://example.org/qore')]:
            variant = copy.deepcopy(self.manifest)
            variant['packages'][0][field] = value
            variants.append(variant)
        duplicate = copy.deepcopy(self.manifest)
        duplicate['packages'].append(duplicate['packages'][0])
        variants.append(duplicate)
        missing = copy.deepcopy(self.manifest)
        missing['fixtures'].pop()
        variants.append(missing)
        source_path = copy.deepcopy(self.manifest)
        source_path['fixtures'][0]['path'] = '../arbitrary'
        variants.append(source_path)
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                module.validate(variant)

    def test_install_commands_keep_paths_separate(self):
        path = '/tmp/rpms/a space.rpm'
        self.assertEqual(module.install_command('suse', [path])[-1], path)
        self.assertIn('--no-recommends', module.install_command('suse', [path]))
        for family in ('fedora', 'el'):
            command = module.install_command(family, [path])
            self.assertEqual(command[-1], path)
            self.assertIn('--setopt=install_weak_deps=False', command)


if __name__ == '__main__':
    unittest.main()
