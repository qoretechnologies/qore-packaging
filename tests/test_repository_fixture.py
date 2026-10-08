# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
from contextlib import contextmanager
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import repository_fixture as fixture
loader = importlib.util.spec_from_file_location('repository_installed', ROOT / 'tools/qualify-installed.py')
installed = importlib.util.module_from_spec(loader)
loader.loader.exec_module(installed)


def metadata(directory, packages):
    primary = ET.Element('metadata', xmlns=fixture.NS['pkg'], packages=str(len(packages)))
    for package in packages:
        item = ET.SubElement(primary, 'package')
        ET.SubElement(item, 'name').text = package['name']
        ET.SubElement(item, 'checksum', type='sha256').text = package['sha256']
        ET.SubElement(item, 'location', href=package['filename'])
    repodata = directory / 'repodata'
    repodata.mkdir()
    payload = gzip.compress(ET.tostring(primary), mtime=0)
    (repodata / 'primary.xml.gz').write_bytes(payload)
    index = ET.Element('repomd', xmlns=fixture.NS['repo'])
    item = ET.SubElement(index, 'data', type='primary')
    ET.SubElement(item, 'checksum', type='sha256').text = hashlib.sha256(payload).hexdigest()
    ET.SubElement(item, 'location', href='repodata/primary.xml.gz')
    (repodata / 'repomd.xml').write_bytes(ET.tostring(index))


class RepositoryFixtureTest(unittest.TestCase):
    def setUp(self):
        self.packages = [{'name': 'qore', 'filename': 'qore-3.0-1.x86_64.rpm', 'sha256': 'a' * 64,
                          'phase': 'runtime'}]

    def test_metadata_rejects_changed_package_inventory(self):
        for change in ('none', 'digest', 'name', 'location', 'duplicate', 'extra', 'missing'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                packages = copy.deepcopy(self.packages)
                if change == 'digest':
                    packages[0]['sha256'] = 'b' * 64
                elif change == 'name':
                    packages[0]['name'] = 'other'
                elif change == 'location':
                    packages[0]['filename'] = '../qore.rpm'
                elif change == 'duplicate':
                    packages *= 2
                elif change == 'extra':
                    packages.append(dict(packages[0], name='extra'))
                elif change == 'missing':
                    packages = []
                directory = Path(temporary)
                metadata(directory, packages)
                if change == 'none':
                    fixture.check_metadata(directory, self.packages)
                else:
                    with self.assertRaises(ValueError):
                        fixture.check_metadata(directory, self.packages)

    def test_metadata_rejects_unsafe_paths_missing_index_and_tampering(self):
        for change in ('', '/tmp/primary.xml.gz', '../primary.xml.gz', 'repodata/../primary.xml.gz',
                       'wrong-checksum', 'missing-primary', 'duplicate-primary'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                metadata(directory, self.packages)
                path = directory / 'repodata/repomd.xml'
                tree = ET.parse(path)
                entry = tree.getroot()[0]
                if change == 'wrong-checksum':
                    entry.find('repo:checksum', fixture.NS).text = '0' * 64
                elif change == 'missing-primary':
                    entry.set('type', 'filelists')
                elif change == 'duplicate-primary':
                    tree.getroot().append(copy.deepcopy(entry))
                else:
                    entry.find('repo:location', fixture.NS).set('href', change)
                tree.write(path)
                with self.assertRaises(ValueError):
                    fixture.check_metadata(directory, self.packages)

    def test_negative_control_requires_a_signature_failure(self):
        for message in ('repomd.xml GPG signature verification error: Bad PGP signature',
                        "Signature verification failed for file 'repomd.xml' from repository 'fixture'.",
                        'Signature verification failed for repomd.xml'):
            fixture.check_signature_rejection(1, message)
            with self.assertRaises(ValueError):
                fixture.check_signature_rejection(0, message)
        for message in ('connection timed out', 'GPG key download failed', 'no such repository', ''):
            with self.assertRaises(ValueError):
                fixture.check_signature_rejection(1, message)

    def test_requests_leave_transitive_runtime_dependencies_to_solver(self):
        manifest = {'packages': self.packages + [dict(self.packages[0], name='libqore'),
                    dict(self.packages[0], name='qore-devel', phase='sdk')], 'modules': [{'name': 'xml'}]}
        self.assertEqual(fixture.requested_packages(manifest, 'runtime'), ['qore', 'qore-xml-module'])
        self.assertEqual(fixture.requested_packages(manifest, 'sdk'), ['qore-devel'])
        del manifest['modules']
        self.assertEqual(fixture.requested_packages(manifest, 'runtime'), ['qore'])

    def test_selected_versions_include_epoch_release_and_architecture(self):
        expected = 'qore 1:3.0-1.x86_64\n'
        for actual in (expected, 'qore 0:3.0-1.x86_64\n', 'qore 1:3.0-2.x86_64\n',
                       'qore 1:3.0-1.aarch64\n', '', expected * 2):
            with self.subTest(actual=actual):
                def run(name, command):
                    return expected if '-qp' in command else actual
                if actual == expected:
                    fixture.verify_selected_versions(self.packages, Path('/repo'), run)
                else:
                    with self.assertRaises(ValueError):
                        fixture.verify_selected_versions(self.packages, Path('/repo'), run)

    def test_repository_cleanup_on_success_and_failures(self):
        for family in ('fedora', 'suse', 'el'):
            for failure in ('none', 'key', 'sign', 'negative', 'refresh', 'consumer'):
                with self.subTest(family=family, failure=failure), tempfile.TemporaryDirectory() as temporary:
                    root = Path(temporary)
                    repository = root / 'rpms'
                    repository.mkdir()
                    output = root / 'output'
                    output.mkdir()
                    configs = root / 'configs'
                    configs.mkdir()
                    (configs / 'existing.repo').write_text('unchanged')
                    key = root / 'obs.asc'
                    key.write_text('OBS public key fixture')
                    private = []
                    commands = []

                    def run(name, command, **kwargs):
                        commands.append((name, command, kwargs))
                        if name == 'repository-create':
                            metadata(repository, self.packages)
                        if name == 'repository-key-create':
                            signer = Path(command[command.index('--homedir') + 1])
                            private.append(signer)
                            (signer / 'private-test.key').write_text('test material')
                        if name == 'repository-key-list':
                            return 'fpr:::::::::' + 'A' * 40 + ':\n'
                        if name == 'repository-key-export':
                            Path(command[command.index('--output') + 1]).write_text('public test key')
                        if name == 'repository-sign':
                            Path(command[command.index('--output') + 1]).write_text('test signature')
                        if name == 'repository-reject-tampered':
                            self.assertTrue(kwargs['reject_signature'])
                            bad = list(root.glob('bad-repository-*'))
                            self.assertEqual(len(bad), 1)
                            self.assertNotEqual((repository / 'repodata/repomd.xml').read_bytes(),
                                                (bad[0] / 'repodata/repomd.xml').read_bytes())
                        fail_at = {'key': 'repository-key-create', 'sign': 'repository-sign',
                                   'negative': 'repository-reject-tampered', 'refresh': 'repository-refresh'}
                        if name == fail_at.get(failure):
                            raise RuntimeError('injected ' + failure)
                        return ''

                    def exercise():
                        with fixture.signed_repository({'family': family, 'packages': self.packages},
                                repository, key, output, run, {'LC_ALL': 'C'}, configs) as result:
                            self.assertFalse(result['private_key_retained'])
                            self.assertTrue(all(not p.exists() for p in private))
                            entries = list(configs.glob('qore-*.repo'))
                            self.assertEqual(len(entries), 1)
                            text = entries[0].read_text()
                            self.assertIn('repo_gpgcheck=1\n', text)
                            self.assertIn('pkg_gpgcheck=1\n', text)
                            self.assertIn('skip_if_unavailable=0\n', text)
                            self.assertFalse(list(root.glob('bad-repository-*')))
                            if failure == 'consumer':
                                raise RuntimeError('injected consumer')
                    if failure == 'none':
                        exercise()
                    else:
                        with self.assertRaisesRegex(RuntimeError, 'injected'):
                            exercise()
                    self.assertTrue(all(not p.exists() for p in private))
                    self.assertEqual(list(configs.iterdir()), [configs / 'existing.repo'])
                    self.assertEqual((configs / 'existing.repo').read_text(), 'unchanged')
                    self.assertIn('repository-agent-stop', [name for name, _, _ in commands])

    def test_native_runner_repository_mode_preserves_installation_gates(self):
        for family in ('fedora', 'suse'):
            with self.subTest(family=family), tempfile.TemporaryDirectory() as temporary:
                target = 'leap' if family == 'suse' else 'fedora'
                manifest = json.loads((ROOT / f'qualification/core21-{target}-aarch64.json').read_text())
                commands = []
                contexts = []

                def fetch(url, digest, path):
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text('verified fixture')

                def logged(command, path, **kwargs):
                    commands.append(command)
                    path.write_text('Header V4 RSA/SHA256 Signature, key ID 12345678: OK\n'
                                    if command[0] == 'rpmkeys' else '')
                    return subprocess.CompletedProcess(command, 0)

                @contextmanager
                def repository(*args):
                    contexts.append('enter')
                    try:
                        yield {'private_key_retained': False}
                    finally:
                        contexts.append('exit')

                with (patch.object(installed.platform, 'machine', return_value='aarch64'),
                      patch.object(installed.os, 'geteuid', return_value=0),
                      patch.object(installed.shutil, 'which', return_value='/fixture/tool'),
                      patch.object(installed, 'fetch_source', side_effect=fetch),
                      patch.object(installed, 'run_logged', side_effect=logged),
                      patch.object(installed, 'installation_environment', return_value={}),
                      patch.object(installed.pwd, 'getpwnam', return_value=SimpleNamespace(pw_uid=123, pw_gid=123)),
                      patch.object(installed.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)),
                      patch.object(fixture, 'signed_repository', side_effect=repository),
                      patch.object(fixture, 'verify_selected_versions') as selected):
                    result = installed.qualify(manifest, Path(temporary) / 'output', repository_install=True)
                self.assertEqual(contexts, ['enter', 'exit'])
                self.assertEqual(result['exit_code'], 0)
                self.assertEqual(selected.call_count, 2)
                installs = [c for c in commands if 'install' in c]
                self.assertEqual(len(installs), 2)
                self.assertEqual(installs[0][-1], 'qore')
                self.assertFalse(any(p.endswith('.rpm') for c in installs for p in c))
                self.assertEqual('--allow-vendor-change' in installs[0], family == 'suse')
                self.assertEqual(len([c for c in commands if c[0] == 'runuser']), 5)


if __name__ == '__main__':
    unittest.main()
