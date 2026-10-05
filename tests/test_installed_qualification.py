# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
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

    def test_missing_unprivileged_runner_is_diagnosed_before_installation(self):
        with patch.object(module.shutil, 'which', side_effect=lambda name: None if name == 'runuser' else '/bin/' + name):
            with self.assertRaisesRegex(ValueError, 'fixture commands: runuser'):
                module.check_prerequisites('fedora')

    def test_prerequisite_inventory_uses_distribution_package_manager(self):
        with patch.object(module.shutil, 'which', side_effect=lambda name: '/bin/' + name) as which:
            module.check_prerequisites('suse')
        self.assertIn(unittest.mock.call('zypper'), which.call_args_list)
        self.assertNotIn(unittest.mock.call('dnf'), which.call_args_list)

    def add_modules(self):
        self.manifest['modules'] = []
        for name in ('uuid', 'process'):
            commit = 'd' * 40
            self.manifest['modules'].append({'name': name, 'commit': commit,
                'fixtures': [{'path': path, 'sha256': 'e' * 64,
                    'url': f'https://raw.githubusercontent.com/qoretechnologies/module-{name}/{commit}/{path}'}
                    for path in sorted(module.MODULE_FIXTURES[name])]})
            self.manifest['packages'].append({'name': 'qore-' + name + '-module',
                'filename': 'qore-' + name + '-module-1-1.aarch64.rpm', 'phase': 'runtime',
                'sha256': 'f' * 64, 'url': 'https://example.org/' + name})

    def test_complete_module_manifest(self):
        self.add_modules()
        self.assertEqual(module.validate(self.manifest), self.manifest)

    def test_module_fixtures_reject_unpinned_incomplete_or_crossed_sources(self):
        self.add_modules()
        for mutation in ('duplicate', 'name', 'commit', 'missing', 'duplicate-file',
                         'path', 'url', 'hash', 'missing-package', 'phase'):
            manifest = copy.deepcopy(self.manifest)
            suite = manifest['modules'][0]
            if mutation == 'duplicate':
                manifest['modules'].append(copy.deepcopy(suite))
            elif mutation == 'name':
                suite['name'] = '../unreviewed'
            elif mutation == 'commit':
                suite['commit'] = 'develop'
            elif mutation == 'missing':
                suite['fixtures'].pop()
            elif mutation == 'duplicate-file':
                suite['fixtures'].append(copy.deepcopy(suite['fixtures'][0]))
            elif mutation == 'path':
                suite['fixtures'][0]['path'] = '../outside'
            elif mutation == 'url':
                suite['fixtures'][0]['url'] = suite['fixtures'][0]['url'].replace('d' * 40, 'a' * 40)
            elif mutation == 'hash':
                suite['fixtures'][0]['sha256'] = ''
            elif mutation == 'missing-package':
                manifest['packages'] = [p for p in manifest['packages'] if p['name'] != 'qore-uuid-module']
            else:
                next(p for p in manifest['packages'] if p['name'] == 'qore-uuid-module')['phase'] = 'sdk'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                module.validate(manifest)

    def test_module_commands_keep_runtime_free_of_compilation(self):
        directory = Path('/tmp/module tests')
        for name in ('uuid', 'process'):
            commands = module.module_commands(name, 'runtime', directory)
            self.assertEqual(len(commands), 1)
            self.assertEqual(commands[0][1][:3], ['qore', '-b', '--enable-debug'])
            self.assertEqual(commands[0][1][3], str(directory / 'test' / ('uuid-test.qtest' if name == 'uuid' else 'process.qtest')))
        commands = module.module_commands('process', 'sdk', directory, Path('/usr/lib64/process.qmod'))
        self.assertEqual([c[0] for c in commands], ['tests', 'compiler', 'state'])
        self.assertEqual(commands[2][1][-2:], ['--module', '/usr/lib64/process.qmod'])
        self.assertEqual([c[0] for c in module.module_commands('uuid', 'sdk', directory)], ['tests', 'compiler'])
        for binary in (None, Path('relative.qmod'), Path('/tmp/unexpected.so')):
            with self.subTest(binary=binary), self.assertRaises(ValueError):
                module.module_commands('process', 'sdk', directory, binary)

    def test_module_download_failure_precedes_installation(self):
        self.add_modules()

        def fetch(url, digest, path):
            if '/module-uuid/' in url:
                raise ValueError('fixture checksum mismatch')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('verified fixture')

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'output'
            with (patch.object(module.platform, 'machine', return_value='aarch64'),
                  patch.object(module.os, 'geteuid', return_value=0),
                  patch.object(module, 'check_prerequisites'),
                  patch.object(module, 'fetch_source', side_effect=fetch),
                  patch.object(module.subprocess, 'run') as run):
                with self.assertRaisesRegex(ValueError, 'fixture checksum mismatch'):
                    module.qualify(self.manifest, output)
                run.assert_not_called()
            self.assertIn('fixture checksum mismatch', (output / 'qualification.json').read_text())


if __name__ == '__main__':
    unittest.main()
