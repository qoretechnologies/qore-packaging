# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
import copy
import importlib.util
import os
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
    def test_fixture_log_preserves_reopened_stdout_and_stderr(self):
        script = '''import os
os.write(1, b'before\\n')
saved = os.open('/proc/self/fd/1', os.O_WRONLY)
os.dup2(saved, 1)
os.close(saved)
os.write(1, b'after\\n')
os.write(2, b'diagnostic\\n')
'''
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / 'output.log'
            result = module.run_logged([sys.executable, '-c', script], log,
                                       owner=(os.getuid(), os.getgid()))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(log.read_bytes(), b'before\nafter\ndiagnostic\n')

    def test_fixture_log_streams_large_output_and_retains_failure(self):
        script = 'import os; os.write(1, b"x" * 1048576); os.write(2, b"failure"); raise SystemExit(7)'
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / 'output.log'
            result = module.run_logged([sys.executable, '-c', script], log,
                                       owner=(os.getuid(), os.getgid()))
            self.assertEqual(result.returncode, 7)
            self.assertEqual(log.read_bytes(), b'x' * 1048576 + b'failure')

    def test_fixture_log_failure_closes_descriptors_without_starting_child(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / 'output.log'
            before = set(os.listdir('/proc/self/fd'))
            with (patch.object(module.os, 'fchown', side_effect=PermissionError('owner')),
                  patch.object(module.subprocess, 'Popen') as start):
                with self.assertRaises(PermissionError):
                    module.run_logged(['not-started'], log, owner=(os.getuid(), os.getgid()))
                start.assert_not_called()
            self.assertEqual(set(os.listdir('/proc/self/fd')), before)
            with self.assertRaises(FileNotFoundError):
                module.run_logged(['/nonexistent/qore-fixture'], log,
                                  owner=(os.getuid(), os.getgid()))
            self.assertEqual(set(os.listdir('/proc/self/fd')), before)

    def test_fixture_log_write_failure_terminates_child_and_closes_descriptors(self):
        with tempfile.TemporaryDirectory() as temporary:
            log = Path(temporary) / 'output.log'
            before = set(os.listdir('/proc/self/fd'))
            with patch.object(module.shutil, 'copyfileobj', side_effect=OSError('full')):
                with self.assertRaisesRegex(OSError, 'full'):
                    module.run_logged([sys.executable, '-c', 'import os; os.read(0, 1)'],
                                      log, owner=(os.getuid(), os.getgid()))
            self.assertEqual(set(os.listdir('/proc/self/fd')), before)

    def setUp(self):
        self.manifest = {'schema': 1, 'family': 'fedora', 'arch': 'aarch64', 'core_commit': 'a' * 40,
                         'signing_key': {'url': 'https://example.org/key.asc', 'sha256': 'f' * 64},
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
            self.assertIn('--setopt=gpgcheck=True', command)
            self.assertIn('--setopt=localpkg_gpgcheck=True', command)
        for family in ('suse', 'fedora', 'el'):
            self.assertFalse({'--nogpgcheck', '--no-gpg-checks', '--allow-unsigned-rpm'}
                             & set(module.install_command(family, [path])))

    def test_signing_key_requires_complete_https_pin(self):
        for key in (None, [], {}, {'url': 'https://example.org/key.asc'},
                    {'url': 'http://example.org/key.asc', 'sha256': 'f' * 64},
                    {'url': 'https://example.org/key.asc', 'sha256': 'bad'}):
            manifest = copy.deepcopy(self.manifest)
            if key is None:
                del manifest['signing_key']
            else:
                manifest['signing_key'] = key
            with self.subTest(key=key), self.assertRaises(ValueError):
                module.validate(manifest)

    def test_unsigned_rpm_digests_are_not_signatures(self):
        for output in ('Payload SHA256 digest: OK\n', '',
                       'Header V3 RSA/SHA256 Signature, key ID 10df018c: NOKEY\n',
                       'Header V3 RSA/SHA256 Signature, key ID 10df018c: BAD\n',
                       'Header OpenPGP V3 RSA/SHA256 signature, key fingerprint: '
                       '3c3e3e9e0eadde7c47e49c549960899f10df018c: NOKEY\n'):
            with self.subTest(output=output), self.assertRaises(ValueError):
                module.require_rpm_signature(output)
        for version in ('3', '4', '6'):
            module.require_rpm_signature('test.rpm:\n    Header V' + version
                + ' RSA/SHA256 Signature, key ID 10df018c: OK\n    Payload SHA256 digest: OK\n')
        module.require_rpm_signature('    Header OpenPGP V3 RSA/SHA256 signature, key fingerprint: '
            '3c3e3e9e0eadde7c47e49c549960899f10df018c: OK\n')

    def test_leap_installs_documentation_without_changing_system_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = root / 'system.conf'
            for settings in ('rpm.install.excludedocs = yes\n',
                             '# rpm.install.excludedocs = yes\n',
                             'rpm.install.excludedocs = no\n'):
                original = 'solver.onlyRequires = true\n' + settings
                config.write_text(original)
                environment = module.installation_environment('suse', root, config)
                actual = Path(environment['ZYPP_CONF']).read_text()
                self.assertEqual(config.read_text(), original)
                self.assertIn('solver.onlyRequires = true', actual)
                self.assertIn('rpm.install.excludedocs = no', actual)
                self.assertNotIn('\nrpm.install.excludedocs = yes', actual)
            self.assertEqual(module.installation_environment('fedora', root, root / 'absent'),
                             dict(module.os.environ))

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
        self.manifest['packages'].append({'name': 'qore-xml-module',
            'filename': 'qore-xml-module-1-1.aarch64.rpm', 'phase': 'runtime',
            'sha256': 'f' * 64, 'url': 'https://example.org/xml'})
        for name in module.MODULE_FIXTURES:
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

    def test_xmlsec_requires_pinned_xml_dependency_before_installation(self):
        self.add_modules()
        for mutation in ('missing', 'sdk', 'unhashed', 'insecure'):
            manifest = copy.deepcopy(self.manifest)
            dependency = next(p for p in manifest['packages'] if p['name'] == 'qore-xml-module')
            if mutation == 'missing':
                manifest['packages'].remove(dependency)
            elif mutation == 'sdk':
                dependency['phase'] = 'sdk'
            elif mutation == 'unhashed':
                dependency.pop('sha256')
            else:
                dependency['url'] = 'http://example.org/xml'
            with self.subTest(mutation=mutation), patch.object(module.subprocess, 'run') as run:
                with self.assertRaises(ValueError):
                    module.qualify(manifest, 'not-created')
                run.assert_not_called()

    def test_xmlsec_uses_installed_runner_and_complete_key_fixtures(self):
        directory = Path('/tmp/XML Security fixtures')
        runtime = module.module_commands('xmlsec', 'runtime', directory)
        self.assertEqual(runtime, [('tests', ['python3', '-B', '-W', 'error',
            '/tmp/XML Security fixtures/rpm/run-tests.py', '--installed'])])
        self.assertEqual(module.module_commands('xmlsec', 'sdk', directory),
                         [('tests', runtime[0][1] + ['--compiler'])])
        self.assertEqual(module.MODULE_FIXTURES['xmlsec'], {'rpm/run-tests.py',
            'debian/tests/compiler', 'test/xmlsec.qtest', 'test/test-cert.pem', 'test/test-key.pem'})
        for family in ('fedora', 'suse', 'el'):
            self.assertEqual(module.module_dependencies('xmlsec', 'runtime', family), [])
            self.assertEqual(module.module_dependencies('xmlsec', 'sdk', family), [])

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

    def test_simple_module_suites_run_all_installed_tests_with_debugging(self):
        directory = Path('/tmp/installed module fixtures')
        expected = {
            'markdown': ['markdown'], 'sysconf': ['sysconf'], 'magic': ['magic'],
            'sqlite3': ['basic'],
            'msgpack': ['msgpack'],
            'kalman': ['extended-filter', 'factories', 'linear-filter', 'matrix'],
        }
        for name, suites in expected.items():
            with self.subTest(module=name):
                commands = module.module_commands(name, 'runtime', directory)
                self.assertEqual([suite for suite, _ in commands], suites)
                for suite, command in commands:
                    self.assertEqual(command[:3], ['qore', '-b', '--enable-debug'])
                    self.assertEqual(command[3], str(directory / 'test' / (suite + '.qtest')))
                    self.assertEqual(command[4], '-v')
                self.assertEqual(module.module_dependencies(name, 'runtime', 'fedora'), [])
                sdk = module.module_commands(name, 'sdk', directory)
                self.assertEqual(sdk[:len(commands)], commands)
                if name == 'markdown':
                    self.assertEqual(sdk[-2:], [
                        ('compiler', ['qcc', '-o', str(directory / 'markdown-compiled'),
                                      str(directory / 'rpm/compiler.qr')]),
                        ('compiled-tests', [str(directory / 'markdown-compiled')]),
                    ])
                else:
                    self.assertEqual(sdk[-1], ('compiler', [str(directory / 'debian/tests/compiler')]))
        sqlite = module.module_commands('sqlite3', 'runtime', directory)[0][1]
        self.assertEqual(sqlite[-2:], ['--db', str(directory / 'qualification.sqlite')])

    def test_treesitter_checks_installed_queries_with_debugging_and_compiler(self):
        directory = Path('/tmp/installed tree fixtures')
        runtime = module.module_commands('treesitter', 'runtime', directory)
        self.assertEqual(runtime, [('tests', ['env', '-u', 'QORE_TREESITTER_QUERY_DIR',
            'qore', '-b', '--enable-debug', '/tmp/installed tree fixtures/test/treesitter.qtest', '-v'])])
        self.assertEqual(module.module_commands('treesitter', 'sdk', directory), runtime + [
            ('compiler', ['/tmp/installed tree fixtures/debian/tests/compiler'])])
        self.assertEqual(module.MODULE_FIXTURES['treesitter'],
                         {'test/treesitter.qtest', 'debian/tests/compiler'})
        for family in ('fedora', 'suse', 'el'):
            self.assertEqual(module.module_dependencies('treesitter', 'runtime', family), [])

    def test_ssh2_uses_private_server_and_compiles_only_with_sdk(self):
        directory = Path('/tmp/SSH2 installed fixtures')
        runtime = module.module_commands('ssh2', 'runtime', directory)
        self.assertEqual(runtime, [('tests', ['python3', '-B', '-W', 'error',
            '/tmp/SSH2 installed fixtures/rpm/run-tests.py', '--installed'])])
        self.assertEqual(module.module_commands('ssh2', 'sdk', directory), runtime + [
            ('compiler', ['/tmp/SSH2 installed fixtures/debian/tests/compiler'])])
        self.assertEqual(module.MODULE_FIXTURES['ssh2'], {
            'rpm/run-tests.py', 'debian/tests/compiler', 'test/NegativeTests.qtest',
            'test/SFTPClient.qtest', 'test/SftpClientDataProvider.qtest',
            'test/SftpPollGetFile.qtest', 'test/SftpPoller.qtest',
            'test/SftpPollerMultiDirs.qtest', 'test/Ssh2Client.qtest',
            'test/Ssh2Connections.qtest'})
        for family in ('fedora', 'suse', 'el'):
            self.assertEqual(module.module_dependencies('ssh2', 'runtime', family),
                             ['openssh-server', 'openssh-clients', 'nss_wrapper'])
            self.assertEqual(module.module_dependencies('ssh2', 'sdk', family), [])

    def test_proj_requires_pinned_geos_before_any_install(self):
        self.add_modules()
        for mutation in ('missing', 'sdk', 'unhashed', 'insecure'):
            manifest = copy.deepcopy(self.manifest)
            dependency = next(p for p in manifest['packages'] if p['name'] == 'qore-geos-module')
            if mutation == 'missing':
                manifest['packages'].remove(dependency)
            elif mutation == 'sdk':
                dependency['phase'] = 'sdk'
            elif mutation == 'unhashed':
                dependency.pop('sha256')
            else:
                dependency['url'] = 'http://example.org/geos'
            with self.subTest(mutation=mutation), patch.object(module.subprocess, 'run') as run:
                with self.assertRaises(ValueError):
                    module.qualify(manifest, 'not-created')
                run.assert_not_called()

    def test_proj_keeps_optional_python_case_and_installed_aot_preload(self):
        self.assertEqual(module.MODULE_FIXTURES['proj'], {
            'test/proj.qtest', 'test/projgeos.qtest', 'test/proj-python.qtest',
            'debian/tests/compiler'})
        directory = Path('/tmp/PROJ installed fixtures')
        files = '/usr/lib64/qore-modules/ProjGeos/ProjGeos.qmod'
        commands = module.module_commands('proj', 'runtime', directory, installed_files=files)
        self.assertEqual([name for name, command in commands], ['proj-python', 'proj', 'projgeos'])
        for name, command in commands:
            self.assertEqual(command, ['qore', '-b', '--enable-debug', '-l', files,
                                      str(directory / 'test' / (name + '.qtest')), '-v'])
        self.assertEqual(module.module_commands('proj', 'sdk', directory, installed_files=files),
                         commands + [('compiler', [str(directory / 'debian/tests/compiler')])])

    def test_pgsql_uses_private_fixture_and_installed_compiler(self):
        directory = Path('/tmp/installed PostgreSQL fixtures')
        for family in ('fedora', 'suse', 'el'):
            with self.subTest(family=family):
                vector = 'QORE_TEST_REQUIRE_PGVECTOR=' + ('1' if family == 'fedora' else '0')
                runtime = module.module_commands('pgsql', 'runtime', directory, family=family)
                self.assertEqual(runtime, [('tests', ['env', vector,
                    'QORE_RPM_TEST_TMP=/tmp/installed PostgreSQL fixtures/runtime-fixture',
                    '/tmp/installed PostgreSQL fixtures/rpm/tests-installed-runtime'])])
                sdk = module.module_commands('pgsql', 'sdk', directory, family=family)
                self.assertEqual(sdk, runtime + [
                    ('compiler', ['qcc', '-o', str(directory / 'pgsql-compiled'),
                                  str(directory / 'rpm/compiler.qr')]),
                    ('compiled-tests', ['env', vector, 'python3', '-B', '-W', 'error',
                        str(directory / 'rpm/with-postgres.py'), '--', str(directory / 'pgsql-compiled'), '-v']),
                ])
                self.assertEqual(module.module_dependencies('pgsql', 'runtime', family),
                                 ['postgresql-server'] + (['pgvector'] if family == 'fedora' else []))
                self.assertEqual(module.module_dependencies('pgsql', 'sdk', family), [])
        self.assertEqual(module.MODULE_FIXTURES['pgsql'], {
            'rpm/tests-installed-runtime', 'rpm/run-suites', 'rpm/with-postgres.py', 'rpm/compiler.qr',
            'test/pgsql.qtest', 'test/pgsql-native-bulk-load.qtest',
            'test/pgsql-cancel-callback.qtest', 'test/pgsql-mutation-observer.qtest'})
        for family in (None, '', 'debian', '../fedora'):
            with self.subTest(family=family), self.assertRaisesRegex(ValueError, 'supported distribution'):
                module.module_commands('pgsql', 'runtime', directory, family=family)

    def test_every_added_suite_rejects_incomplete_fixtures(self):
        self.add_modules()
        for entry in self.manifest['modules']:
            manifest = copy.deepcopy(self.manifest)
            changed = next(item for item in manifest['modules'] if item['name'] == entry['name'])
            changed['fixtures'].pop()
            with self.subTest(module=entry['name']), self.assertRaisesRegex(ValueError, 'complete module fixture'):
                module.validate(manifest)

    def test_aot_module_suites_preload_only_installed_inventory_paths(self):
        directory = Path('/tmp/installed modules')
        expected_counts = {'fsevent': 7, 'tar': 3, 'zip': 2, 'cairo': 2, 'geos': 2,
                           'git': 16, 'imagemagick': 2, 'proj': 3}
        for name, count in expected_counts.items():
            suffixes = module.MODULE_PRELOADS[name]
            files = '\n'.join('/usr/lib64/qore-modules/3.0.0' + suffix for suffix in suffixes)
            with self.subTest(module=name):
                commands = module.module_commands(name, 'runtime', directory, installed_files=files)
                qtests = [command for _, command in commands if any(arg.endswith('.qtest') for arg in command)]
                self.assertEqual(len(qtests), count)
                for command in qtests:
                    self.assertIn('--enable-debug', command)
                    self.assertIn('-b', command)
                    for suffix in suffixes:
                        index = command.index('/usr/lib64/qore-modules/3.0.0' + suffix)
                        self.assertEqual(command[index - 1], '-l')
                self.assertFalse(any('qcc' in command for _, command in commands))
                sdk = module.module_commands(name, 'sdk', directory, installed_files=files)
                self.assertEqual(sdk[:-1], commands)
                self.assertEqual(sdk[-1][0], 'compiler')
                for invalid in ('', files + '\n' + files, files.replace('/usr/', 'relative/')):
                    with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                        module.module_commands(name, 'runtime', directory, installed_files=invalid)

    def test_archive_cli_and_all_codec_checks_use_installed_commands(self):
        directory = Path('/tmp/archive fixtures')
        files = '/usr/lib64/qore-modules/3.0.0/TarDataProvider/TarDataProvider.qmod'
        tar = dict(module.module_commands('tar', 'runtime', directory, installed_files=files))
        self.assertEqual(tar['qtar'][:3], ['env', 'QORE_QTAR_BINARY=/usr/bin/qtar', 'QORE_MODULE_DIR='])
        files = '/usr/lib64/qore-modules/3.0.0/ZipDataProvider/ZipDataProvider.qmod'
        zip_commands = dict(module.module_commands('zip', 'runtime', directory, installed_files=files))
        self.assertEqual(zip_commands['features'], ['qore', '-b', '--enable-debug',
                         '/tmp/archive fixtures/debian/tests/features', '-v'])
        self.assertEqual(zip_commands['cli'], ['/bin/sh',
                         '/tmp/archive fixtures/debian/tests/cli', '/usr/bin/qzip'])
        for family in ('fedora', 'suse', 'el'):
            self.assertEqual(module.module_dependencies('zip', 'runtime', family), ['unzip', 'diffutils'])
            self.assertEqual(module.module_dependencies('zip', 'sdk', family), [])

    def test_ncurses_installed_suite_retains_terminal_and_dependency_checks(self):
        directory = Path('/tmp/ncurses fixtures')
        commands = module.module_commands('ncurses', 'runtime', directory)
        self.assertEqual(commands, [('tests', ['env',
            'QORE_RPM_TEST_TMP=/tmp/ncurses fixtures/runtime-fixture',
            '/tmp/ncurses fixtures/rpm/tests-installed/runtime'])])
        self.assertEqual(module.module_commands('ncurses', 'sdk', directory), commands + [
            ('compiler', ['/tmp/ncurses fixtures/debian/tests/compiler'])])
        self.assertEqual(len([p for p in module.MODULE_FIXTURES['ncurses'] if p.endswith('.qtest')]), 11)
        self.assertIn('test/TestHarness.qc', module.MODULE_FIXTURES['ncurses'])

    def test_ssh_fixture_uses_installed_modules_and_compiles_only_in_sdk_phase(self):
        directory = Path('/tmp/SSH fixtures')
        runtime = module.module_commands('ssh', 'runtime', directory)
        self.assertEqual(runtime, [('tests', ['python3', '-B', '-W', 'error',
            '/tmp/SSH fixtures/rpm/run-tests.py', '--installed'])])
        self.assertEqual(module.module_commands('ssh', 'sdk', directory),
                         [('tests', runtime[0][1] + ['--compiler'])])
        fixtures = module.MODULE_FIXTURES['ssh']
        self.assertEqual(len([p for p in fixtures if p.startswith('test/') and p.endswith('.qtest')]), 15)
        self.assertEqual(len([p for p in fixtures if p.startswith('examples/')]), 6)
        self.assertIn('test/TestLoggerInterface.qm', fixtures)
        self.assertEqual({p for p in fixtures if p.startswith('test/data/')}, {
            'test/data/ssh_client_ed25519_key', 'test/data/ssh_client_ed25519_key.pub',
            'test/data/ssh_host_ed25519_key'})
        for family in ('fedora', 'suse', 'el'):
            self.assertEqual(module.module_dependencies('ssh', 'runtime', family), ['openssh-clients'])
            self.assertEqual(module.module_dependencies('ssh', 'sdk', family), [])

    def test_vss_fixture_keeps_included_specs_and_runtime_dependency_checks(self):
        directory = Path('/tmp/VSS fixtures')
        runtime = module.module_commands('vss', 'runtime', directory)
        self.assertEqual(runtime, [('tests', ['/tmp/VSS fixtures/rpm/tests-installed/runtime'])])
        self.assertEqual(module.module_commands('vss', 'sdk', directory), runtime + [
            ('compiler', ['/tmp/VSS fixtures/debian/tests/compiler'])])
        fixtures = module.MODULE_FIXTURES['vss']
        self.assertEqual(len([p for p in fixtures if p.endswith('.qtest')]), 7)
        self.assertEqual(len([p for p in fixtures if p.startswith('test/data/')]), 13)
        for path in ('main.vspec', 'Cabin/Cabin.vspec', 'Powertrain/Powertrain.vspec'):
            self.assertIn('test/data/with_includes/' + path, fixtures)

    def test_graphics_cli_uses_installed_programs(self):
        directory = Path('/tmp/graphics and messaging')
        for name, variable, program in [('cairo', 'QORE_QSVG_BINARY', '/usr/bin/qsvg'),
                                         ('imagemagick', 'QORE_QIMAGE_BINARY', '/usr/bin/qimage')]:
            files = '/usr/lib64' + module.MODULE_PRELOADS[name][0]
            commands = dict(module.module_commands(name, 'runtime', directory, installed_files=files))
            self.assertEqual(commands['cli'], ['env', variable + '=' + program,
                '/bin/sh', str(directory / 'debian/tests/cli')])
            for family, font in [('suse', 'dejavu-fonts'), ('fedora', 'dejavu-sans-fonts'),
                                  ('el', 'dejavu-sans-fonts')]:
                self.assertEqual(module.module_dependencies(name, 'runtime', family), [font, 'diffutils'])
                self.assertEqual(module.module_dependencies(name, 'sdk', family), [])


    def test_zmq_installed_checks_preserve_features_and_strict_sandbox_diagnostics(self):
        directory = Path('/tmp/ZeroMQ fixtures')
        binary = Path('/usr/lib64/qore-modules/zmq-api-2.0.qmod')
        runtime = module.module_commands('zmq', 'runtime', directory, binary)
        self.assertEqual(runtime, [
            ('tests', ['env', 'QORE_RPM_TEST_TMP=/tmp/ZeroMQ fixtures/runtime-fixture',
                       '/tmp/ZeroMQ fixtures/rpm/tests-installed-runtime']),
            ('sandbox-errors', ['python3', '-B', '-W', 'error',
                '/tmp/ZeroMQ fixtures/test/run-sandbox-errors.py', '--module', str(binary),
                '--allow-qunit-xml-fallback']),
        ])
        self.assertEqual(module.module_commands('zmq', 'sdk', directory, binary), runtime + [
            ('compiler', ['/tmp/ZeroMQ fixtures/debian/tests/compiler'])])
        self.assertEqual(len([p for p in module.MODULE_FIXTURES['zmq'] if p.endswith('.qtest')]), 5)
        self.assertIn('rpm/features.qr', module.MODULE_FIXTURES['zmq'])

    def test_zmq_requires_installed_binary_in_both_phases(self):
        for phase in ('runtime', 'sdk'):
            for binary in (None, Path('relative.qmod'), Path('/tmp/library.so')):
                with self.subTest(phase=phase, binary=binary), self.assertRaisesRegex(ValueError, 'module path'):
                    module.module_commands('zmq', phase, Path('/tmp/fixtures'), binary)

    def test_odbc_runtime_and_sdk_cover_installed_arrays_and_native_failures(self):
        directory = Path('/tmp/ODBC fixtures')
        runtime = module.module_commands('odbc', 'runtime', directory)
        self.assertEqual(runtime, [('tests', ['env',
            'QORE_RPM_TEST_TMP=/tmp/ODBC fixtures/runtime-fixture',
            '/tmp/ODBC fixtures/rpm/tests-installed-runtime'])])
        commands = dict(module.module_commands('odbc', 'sdk', directory,
            Path('/usr/lib64/odbc-api-2.0.qmod'), Path('/usr/lib64/psqlodbcw.so')))
        self.assertEqual(commands['tests'], runtime[0][1])
        self.assertEqual(commands['native'], ['env',
            'QORE_ODBC_BINARY_MODULE=/usr/lib64/odbc-api-2.0.qmod',
            '/tmp/ODBC fixtures/rpm/test-postgres', '/tmp/ODBC fixtures/test', '--native'])
        self.assertEqual(commands['compiler'], ['qcc', '-o',
            '/tmp/ODBC fixtures/array-binding-compiled', '/tmp/ODBC fixtures/test/array-binding.qtest'])
        self.assertEqual(commands['compiled-tests'], ['python3', '-B',
            '/tmp/ODBC fixtures/rpm/with-postgres.py', '--driver', '/usr/lib64/psqlodbcw.so',
            '--', '/tmp/ODBC fixtures/array-binding-compiled', '-v'])

    def test_odbc_commands_reject_missing_or_relative_installed_files(self):
        for binary in (None, Path('relative.qmod'), Path('/tmp/module.so')):
            with self.subTest(binary=binary), self.assertRaisesRegex(ValueError, 'module path'):
                module.module_commands('odbc', 'sdk', Path('/tmp/tests'), binary,
                                       Path('/usr/lib64/psqlodbcw.so'))
        for driver in (None, Path('psqlodbcw.so'), Path('/tmp/other.so')):
            with self.subTest(driver=driver), self.assertRaisesRegex(ValueError, 'PostgreSQL driver'):
                module.module_commands('odbc', 'sdk', Path('/tmp/tests'),
                                       Path('/usr/lib64/odbc.qmod'), driver)
        for name, phase in (('unknown', 'runtime'), ('odbc', 'invalid')):
            with self.subTest(name=name, phase=phase), self.assertRaises(ValueError):
                module.module_commands(name, phase, Path('/tmp/tests'))

    def test_fixture_dependencies_preserve_minimal_runtime(self):
        for family in ('suse', 'fedora', 'el'):
            runtime = module.module_dependencies('odbc', 'runtime', family)
            self.assertEqual(runtime, ['postgresql-server',
                'psqlODBC' if family == 'suse' else 'postgresql-odbc'])
            self.assertEqual(module.module_dependencies('odbc', 'sdk', family), ['unixODBC-devel'])
            self.assertFalse(set(runtime) & {'gcc', 'gcc-c++', 'qore-devel', 'unixODBC-devel'})
            self.assertEqual(module.module_dependencies('uuid', 'runtime', family), [])
            self.assertEqual(module.module_dependencies('process', 'runtime', family),
                             ['procps' if family == 'suse' else 'procps-ng'])
        for args in (('unknown', 'runtime', 'suse'), ('odbc', 'bad', 'el'), ('odbc', 'sdk', 'unknown')):
            with self.subTest(args=args), self.assertRaises(ValueError):
                module.module_dependencies(*args)

    def test_installed_inventory_requires_one_absolute_module_or_driver(self):
        self.assertEqual(module.installed_module_file('odbc',
            '/usr/share/licenses/odbc/LICENSE\n/usr/lib64/odbc.qmod\n', '.qmod'),
            Path('/usr/lib64/odbc.qmod'))
        self.assertEqual(module.installed_module_file('driver',
            '/usr/lib64/psqlodbcw.so\n/usr/share/odbc/psqlodbcw.so.example', '/psqlodbcw.so'),
            Path('/usr/lib64/psqlodbcw.so'))
        for files in ('', 'odbc.qmod', '/tmp/../odbc.qmod',
                      '/usr/lib64/a.qmod\n/usr/lib64/b.qmod'):
            with self.subTest(files=files), self.assertRaises(ValueError):
                module.installed_module_file('odbc', files, '.qmod')

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

    def test_odbc_native_header_checksum_failure_precedes_installation(self):
        self.add_modules()
        self.manifest['modules'] = [entry for entry in self.manifest['modules'] if entry['name'] == 'odbc']

        def fetch(url, digest, path):
            if url.endswith('/src/ODBCArraySize.h'):
                raise ValueError('ODBC native header checksum mismatch')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('verified fixture')

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'output'
            with (patch.object(module.platform, 'machine', return_value='aarch64'),
                  patch.object(module.os, 'geteuid', return_value=0),
                  patch.object(module, 'check_prerequisites'),
                  patch.object(module, 'fetch_source', side_effect=fetch),
                  patch.object(module.subprocess, 'run') as run):
                with self.assertRaisesRegex(ValueError, 'ODBC native header checksum mismatch'):
                    module.qualify(self.manifest, output)
                run.assert_not_called()
            self.assertIn('ODBC native header checksum mismatch', (output / 'qualification.json').read_text())

    def test_bad_key_hash_precedes_all_rpm_operations(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'output'
            with (patch.object(module.platform, 'machine', return_value='aarch64'),
                  patch.object(module.os, 'geteuid', return_value=0),
                  patch.object(module, 'check_prerequisites'),
                  patch.object(module, 'fetch_source', side_effect=ValueError('key checksum mismatch')) as fetch,
                  patch.object(module.subprocess, 'run') as run):
                with self.assertRaisesRegex(ValueError, 'key checksum mismatch'):
                    module.qualify(self.manifest, output)
                run.assert_not_called()
                self.assertEqual(fetch.call_args.args[:2],
                                 (self.manifest['signing_key']['url'], self.manifest['signing_key']['sha256']))
            self.assertIn('key checksum mismatch', (output / 'qualification.json').read_text())


if __name__ == '__main__':
    unittest.main()
