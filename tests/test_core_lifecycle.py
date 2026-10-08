# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
from contextlib import contextmanager
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import core_lifecycle as lifecycle
import repository_fixture
loader = importlib.util.spec_from_file_location('lifecycle_installed', ROOT / 'tools/qualify-installed.py')
installed = importlib.util.module_from_spec(loader)
loader.loader.exec_module(installed)


def manifest(target='fedora'):
    return json.loads((ROOT / f'qualification/core21-{target}-aarch64.json').read_text())


class CoreLifecycleTest(unittest.TestCase):
    def test_only_the_complete_core_package_set_can_be_removed(self):
        for target in ('fedora', 'leap', 'el10'):
            original = manifest(target)
            expected = {p['name'] for p in original['packages'] if p['url'].split('/')[-2] == 'qore'}
            self.assertEqual({p['name'] for p in lifecycle.core_packages(original)}, expected)
            for change in ('module', 'missing', 'extra-core', 'renamed', 'wrong-source', 'duplicate'):
                with self.subTest(target=target, change=change):
                    data = copy.deepcopy(original)
                    if change == 'module':
                        data['modules'] = [{'name': 'xml'}]
                    elif change == 'missing':
                        data['packages'].pop(0)
                    elif change == 'extra-core':
                        data['packages'].append(dict(data['packages'][0], name='qore-doc'))
                    elif change == 'renamed':
                        data['packages'][0]['name'] = 'unrelated'
                    elif change == 'wrong-source':
                        data['packages'][0]['url'] = data['packages'][0]['url'].replace('/qore/', '/different/')
                    else:
                        data['packages'].append(data['packages'][0])
                    with self.assertRaises(ValueError):
                        lifecycle.core_packages(data)

    def test_negative_removal_requires_the_exact_dependency_failure(self):
        for library in ('libqore', 'libqore20'):
            text = f'error: Failed dependencies:\n\t{library}(aarch-64) = 3.0-21 is needed by (installed) qore-3.0-21.aarch64\n'
            lifecycle.check_dependency_rejection(1, text, library)
            for code, message in ((0, text), (2, text), (1, 'error: cannot open RPM database'),
                                  (1, text.replace(library, 'another-library')), (1, ''),
                                  (1, text.replace('qore-3.0', 'unrelated-3.0'))):
                with self.subTest(code=code, message=message), self.assertRaises(ValueError):
                    lifecycle.check_dependency_rejection(code, message, library)
        with self.assertRaises(ValueError):
            lifecycle.check_dependency_rejection(1, text, 'unrelated')

    def test_inventory_and_payload_validation(self):
        self.assertEqual(lifecycle.inventory('z\t0:1-1.aarch64\na\t1:2-3.noarch\n'),
                         ['a\t1:2-3.noarch', 'z\t0:1-1.aarch64'])
        for text in ('', 'qore', 'qore\t1\textra', 'qore\t1\nqore\t1\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                lifecycle.inventory(text)
        self.assertEqual(lifecycle.payload_files('/usr/bin/qore\t33261\n/usr/share/qore\t16877\n'
                                                 '/usr/bin/qcc\t41471\n'), ['/usr/bin/qcc', '/usr/bin/qore'])
        for text in ('', '/usr/share/qore\t16877\n', 'relative\t33261\n', '/usr/../tmp/qore\t33261\n',
                     '/usr/bin/qore\tbad\n', '/usr/bin/qore\n'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                lifecycle.payload_files(text)

    def test_removal_checks_package_set_files_symlinks_and_executables(self):
        before = ['other\t0:1-1.x86_64', 'qore\t0:3-21.x86_64']
        after = before[:1]
        with tempfile.TemporaryDirectory() as temporary, patch.object(lifecycle.shutil, 'which', return_value=None):
            path = Path(temporary) / 'payload'
            lifecycle.verify_removed(['qore'], before, after, [str(path)])
            for wrong in (before, [], ['other\t0:2-1.x86_64']):
                with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                    lifecycle.verify_removed(['qore'], before, wrong, [str(path)])
            path.write_text('leftover')
            with self.assertRaisesRegex(ValueError, 'payload survives'):
                lifecycle.verify_removed(['qore'], before, after, [str(path)])
            path.unlink()
            path.symlink_to(Path(temporary) / 'missing-target')
            with self.assertRaisesRegex(ValueError, 'payload survives'):
                lifecycle.verify_removed(['qore'], before, after, [str(path)])
        with patch.object(lifecycle.shutil, 'which', return_value='/usr/local/bin/qore'):
            with self.assertRaisesRegex(ValueError, 'payload survives'):
                lifecycle.verify_removed(['qore'], before, after, [])

    def test_transaction_sequence_and_failures(self):
        for target in ('fedora', 'leap', 'el10'):
            data = manifest(target)
            core = lifecycle.core_packages(data)
            names = [p['name'] for p in core]
            before = '\n'.join([n + '\t0:3.0-21.aarch64' for n in names] + ['dependency\t0:1-2.aarch64']) + '\n'
            for failure in ('none', 'precondition', 'negative-mutated', 'remove', 'unrelated-removed',
                            'reinstall', 'wrong-version', 'inventory-drift', 'rpm-verify'):
                with self.subTest(target=target, failure=failure):
                    commands = []
                    def run(name, command, **kwargs):
                        commands.append((name, command, kwargs))
                        if name == 'lifecycle-reject-library-removal':
                            self.assertEqual(command, ['rpm', '-e', '--test', names[0]])
                            self.assertEqual(kwargs['reject_dependency'], names[0])
                        fail_at = {'remove': 'lifecycle-remove', 'reinstall': 'lifecycle-reinstall',
                                   'rpm-verify': 'lifecycle-rpm-verify'}
                        if name == fail_at.get(failure):
                            raise RuntimeError('injected failure')
                        if name == 'lifecycle-payload':
                            return '/usr/bin/qore\t33261\n'
                        if name == 'lifecycle-removed-inventory':
                            return 'different\t0:1-1.aarch64\n' if failure == 'unrelated-removed' else 'dependency\t0:1-2.aarch64\n'
                        if name in ('lifecycle-before', 'lifecycle-after-rejection', 'lifecycle-restored-inventory'):
                            if ((failure == 'precondition' and name == 'lifecycle-before') or
                                (failure == 'negative-mutated' and name == 'lifecycle-after-rejection')):
                                return 'dependency\t0:1-2.aarch64\n'
                            return before + ('extra\t0:9-1.aarch64\n' if failure == 'inventory-drift'
                                             and name == 'lifecycle-restored-inventory' else '')
                        if name.startswith('lifecycle-repository-header-'):
                            return name.removeprefix('lifecycle-repository-header-') + ' 0:3.0-21.aarch64\n'
                        if name.startswith('lifecycle-repository-selected-'):
                            return name.removeprefix('lifecycle-repository-selected-') + (
                                ' 0:3.0-22.aarch64\n' if failure == 'wrong-version' else ' 0:3.0-21.aarch64\n')
                        return ''
                    with (patch.object(lifecycle.os.path, 'lexists', return_value=False),
                          patch.object(lifecycle.shutil, 'which', return_value=None)):
                        if failure == 'none':
                            result = lifecycle.qualify(data, Path('/rpms'), run, {}, installed.install_command)
                            self.assertTrue(result['exact_inventory_restored'])
                            self.assertEqual(result['core_packages'], names)
                            remove = next(c for n, c, _ in commands if n == 'lifecycle-remove')
                            self.assertIn('remove', remove)
                            self.assertEqual(remove[-7:], names)
                            if target != 'leap':
                                self.assertIn('--setopt=clean_requirements_on_remove=False', remove)
                            reinstall = next(c for n, c, _ in commands if n == 'lifecycle-reinstall')
                            self.assertEqual(reinstall[-7:], names)
                            self.assertFalse(any(p.endswith('.rpm') for p in reinstall))
                            self.assertEqual('--allow-vendor-change' in reinstall, target == 'leap')
                            self.assertEqual(len(commands), len({n for n, _, _ in commands}))
                        else:
                            with self.assertRaises((ValueError, RuntimeError)):
                                lifecycle.qualify(data, Path('/rpms'), run, {}, installed.install_command)

    def test_runner_rejects_unsafe_mode_before_installation(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'out'
            with self.assertRaisesRegex(ValueError, 'requires signed repository'):
                installed.qualify(manifest(), output, core_lifecycle_check=True)
            self.assertFalse(output.exists())

    def test_runner_retests_reinstall_and_cleans_repository_on_failure(self):
        for failure in ('none', 'lifecycle', 'reinstalled-runtime'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as temporary:
                commands, contexts = [], []
                def fetch(url, digest, path):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text('verified fixture')
                def logged(command, path, **kwargs):
                    commands.append(command)
                    path.write_text('Header V4 RSA/SHA256 Signature, key ID 12345678: OK\n'
                                    if command[0] == 'rpmkeys' else '')
                    return subprocess.CompletedProcess(command, 1 if path.stem == failure else 0)
                @contextmanager
                def repository(*args):
                    contexts.append('enter')
                    try:
                        yield {'private_key_retained': False}
                    finally:
                        contexts.append('exit')
                def check(*args):
                    if failure == 'lifecycle':
                        raise ValueError('injected lifecycle failure')
                    return {'exact_inventory_restored': True}
                output = Path(temporary) / 'output'
                with (patch.object(installed.platform, 'machine', return_value='aarch64'),
                      patch.object(installed.os, 'geteuid', return_value=0),
                      patch.object(installed.shutil, 'which', return_value='/fixture/tool'),
                      patch.object(installed, 'fetch_source', side_effect=fetch),
                      patch.object(installed, 'run_logged', side_effect=logged),
                      patch.object(installed, 'installation_environment', return_value={}),
                      patch.object(installed.pwd, 'getpwnam', return_value=SimpleNamespace(pw_uid=123, pw_gid=123)),
                      patch.object(installed.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)),
                      patch.object(repository_fixture, 'signed_repository', side_effect=repository),
                      patch.object(repository_fixture, 'verify_selected_versions'),
                      patch.object(lifecycle, 'qualify', side_effect=check)):
                    if failure == 'none':
                        result = installed.qualify(manifest(), output, repository_install=True, core_lifecycle_check=True)
                        self.assertTrue(result['core_lifecycle']['exact_inventory_restored'])
                        self.assertEqual(len([c for c in commands if c[0] == 'runuser']), 9)
                    else:
                        with self.assertRaises((ValueError, subprocess.CalledProcessError)):
                            installed.qualify(manifest(), output, repository_install=True, core_lifecycle_check=True)
                        self.assertEqual(json.loads((output / 'qualification.json').read_text())['exit_code'], 1)
                self.assertEqual(contexts, ['enter', 'exit'])


if __name__ == '__main__':
    unittest.main()
