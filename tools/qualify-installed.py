#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Qualify pinned OBS RPMs in a disposable native distribution container."""
import argparse
import json
import os
from pathlib import Path
import platform
import pwd
import re
import shutil
import subprocess
import tempfile

from packaging import fetch_source

FIXTURES = {'rpm/tests-installed/' + name for name in ('runtime', 'development', 'tools', 'remote-debuggers')}
FIXTURES.add('modules/ml/test/data/test_linear.onnx')
MODULE_FIXTURES = {
    'cairo': {'test/cairo.qtest', 'test/CairoDataProvider.qtest',
              'debian/tests/cli', 'debian/tests/compiler'},
    'geos': {'test/geos.qtest', 'test/GEOSDataProvider.qtest', 'debian/tests/compiler'},
    'git': {'debian/tests/compiler'} | {'test/' + name + '.qtest' for name in
        ('CornerCases', 'GitBlame', 'GitBranch', 'GitConfigManager', 'GitConnections',
         'GitDataProvider', 'GitDiff', 'GitForgeHelper', 'GitMerge', 'GitMisc',
         'GitRemote', 'GitSecurity', 'GitStash', 'GitVirtual', 'NegativeTests', 'git')},
    'imagemagick': {'test/imagemagick.qtest', 'test/ImageMagickDataProvider.qtest',
                    'debian/tests/cli', 'debian/tests/compiler'},
    'msgpack': {'test/msgpack.qtest', 'debian/tests/compiler'},
    'fsevent': {'debian/tests/compiler'} | {'test/' + name + '.qtest' for name in
        ('FsEventPoller-negative', 'FsEventPoller.qm', 'FsEventPollerUtil',
         'fsevent-corner-cases', 'fsevent-destroy-in-callback', 'fsevent-negative', 'fsevent')},
    'tar': {'test/TarDataProvider.qtest', 'test/qtar.qtest', 'test/tar.qtest',
            'debian/tests/compiler'},
    'zip': {'test/ZipDataProvider.qtest', 'test/zip.qtest', 'debian/tests/compiler',
            'debian/tests/features', 'debian/tests/cli'},
    'ncurses': {'rpm/tests-installed/runtime', 'test/TestHarness.qc', 'debian/tests/compiler'}
        | {'test/ncurses' + suffix + '.qtest' for suffix in
           ('', '-app', '-base', '-components', '-integration', '-layout', '-qrepl',
            '-scroll', '-terminal-text', '-widget', '-wrap')},
    'markdown': {'test/markdown.qtest', 'test/test.md', 'test/test.html', 'rpm/compiler.qr'},
    'sysconf': {'test/sysconf.qtest', 'debian/tests/compiler'},
    'magic': {'test/magic.qtest', 'test/qore.png', 'test/qore.jpg', 'test/qore.txt',
              'debian/tests/compiler'},
    'sqlite3': {'test/basic.qtest', 'test/blob.png', 'debian/tests/compiler'},
    'kalman': {'test/extended-filter.qtest', 'test/factories.qtest',
               'test/linear-filter.qtest', 'test/matrix.qtest', 'debian/tests/compiler'},
    'uuid': {'test/uuid-test.qtest', 'debian/tests/compiler'},
    'process': {'test/process.qtest', 'test/process-state.qtest',
                'test/process-state-fixture.c', 'test/run-process-state.py',
                'debian/tests/compiler'} | {
                    'test/test_' + name + '.q' for name in
                    ('cwd', 'env', 'false', 'io', 'output', 'signal', 'sleep',
                     'stdin_eof', 'true', 'utf8')},
    'odbc': {'rpm/tests-installed-runtime', 'rpm/test-postgres', 'rpm/run-suites',
             'rpm/with-postgres.py', 'test/array-binding.qtest', 'test/odbc.qtest',
             'test/native/run-bind-failure.py', 'test/native/bind-failure.cpp',
             'test/native/bind-failure.qtest', 'test/native/array-size.cpp',
             'src/ODBCArraySize.h'},
}
MODULE_PRELOADS = {
    'cairo': ('/CairoDataProvider/CairoDataProvider.qmod',),
    'geos': ('/GEOSDataProvider/GEOSDataProvider.qmod',),
    'git': ('/GitDataProvider/GitDataProvider.qmod', '/GitConfigManager/GitConfigManager.qmod',
            '/GitForgeHelper/GitForgeHelper.qmod', '/GitConnections.qmod'),
    'imagemagick': ('/ImageMagickDataProvider/ImageMagickDataProvider.qmod',),
    'fsevent': ('/FsEventPollerUtil.qmod', '/FsEventPoller.qmod'),
    'tar': ('/TarDataProvider/TarDataProvider.qmod',),
    'zip': ('/ZipDataProvider/ZipDataProvider.qmod',),
}
SIMPLE_MODULES = ('markdown', 'sysconf', 'magic', 'sqlite3', 'kalman', 'msgpack',
                  'fsevent', 'tar', 'zip', 'cairo', 'geos', 'git', 'imagemagick')


def validate_modules(manifest):
    names = set()
    fixtures = []
    packages = {entry['name']: entry for entry in manifest.get('packages', [])}
    for entry in manifest.get('modules', []):
        name = entry.get('name', '')
        if name not in MODULE_FIXTURES or name in names:
            raise ValueError('Unknown or duplicate installed module suite')
        names.add(name)
        commit = entry.get('commit', '')
        if not re.fullmatch('[0-9a-f]{40}', commit):
            raise ValueError('Module fixtures require an immutable source revision')
        files = entry.get('fixtures', [])
        if ({f.get('path') for f in files} != MODULE_FIXTURES[name]
                or len(files) != len(MODULE_FIXTURES[name])):
            raise ValueError('Expected complete module fixture inventory')
        prefix = f'https://raw.githubusercontent.com/qoretechnologies/module-{name}/{commit}/'
        if any(f.get('url') != prefix + f['path'] for f in files):
            raise ValueError('Module fixture URLs must match their pinned repository revision')
        if packages.get('qore-' + name + '-module', {}).get('phase') != 'runtime':
            raise ValueError('Missing module runtime RPM')
        fixtures.extend(files)
    return fixtures


def validate(manifest):
    if manifest.get('schema') != 1 or manifest.get('family') not in ('fedora', 'suse', 'el'):
        raise ValueError('Unsupported qualification manifest')
    if manifest.get('arch') not in ('aarch64', 'x86_64'):
        raise ValueError('Unsupported native architecture')
    if not re.fullmatch('[0-9a-f]{40}', manifest.get('core_commit', '')):
        raise ValueError('Core fixtures must have an immutable source revision')
    fixtures = manifest.get('fixtures', [])
    if {entry.get('path') for entry in fixtures} != FIXTURES or len(fixtures) != len(FIXTURES):
        raise ValueError('Expected the complete installed fixture inventory')
    names = set()
    key = manifest.get('signing_key', {})
    if not isinstance(key, dict) or set(key) != {'url', 'sha256'}:
        raise ValueError('A pinned RPM signing key is required')
    for entry in fixtures + manifest.get('packages', []) + validate_modules(manifest) + [key]:
        if not re.fullmatch('[0-9a-f]{64}', entry.get('sha256', '')):
            raise ValueError('Every artifact needs a SHA-256 pin')
        if not entry.get('url', '').startswith('https://'):
            raise ValueError('Artifact URLs require HTTPS')
    for entry in manifest.get('packages', []):
        name = entry.get('name', '')
        filename = entry.get('filename', '')
        if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9+._-]*', name) or name in names:
            raise ValueError('Package names must be unique and safe')
        if (Path(filename).name != filename or filename.startswith('.') or
                not filename.endswith(('.' + manifest['arch'] + '.rpm', '.noarch.rpm'))):
            raise ValueError('Expected a binary RPM for the native architecture')
        if entry.get('phase') not in ('runtime', 'sdk'):
            raise ValueError('Package phase must be runtime or sdk')
        names.add(name)
    if not {'qore', 'qore-stdlib', 'qore-devel', 'qore-rpm-macros', 'qore-misc-tools', 'qore-debug-tools'} <= names:
        raise ValueError('Missing core runtime or SDK packages')
    library = 'libqore20' if manifest['family'] == 'suse' else 'libqore'
    if library not in names:
        raise ValueError('Missing the distribution-specific Qore runtime library')
    for entry in manifest['packages']:
        expected = 'sdk' if entry['name'] in {'qore-devel', 'qore-rpm-macros', 'qore-misc-tools', 'qore-debug-tools'} else 'runtime'
        if entry['phase'] != expected:
            raise ValueError('Runtime and SDK phases must remain separate')
    return manifest


def module_dependencies(name, phase, family):
    """Distribution packages needed by reviewed fixtures, separate from RPM requirements."""
    if name not in MODULE_FIXTURES or phase not in ('runtime', 'sdk'):
        raise ValueError('Unknown module suite or phase')
    if family not in ('fedora', 'suse', 'el'):
        raise ValueError('Unsupported fixture distribution')
    if name == 'process':
        return ['procps' if family == 'suse' else 'procps-ng']
    if name == 'odbc':
        return (['postgresql-server', 'psqlODBC' if family == 'suse' else 'postgresql-odbc']
                if phase == 'runtime' else ['unixODBC-devel'])
    if name == 'zip' and phase == 'runtime':
        return ['unzip', 'diffutils']
    if name in ('cairo', 'imagemagick') and phase == 'runtime':
        return ['dejavu-fonts' if family == 'suse' else 'dejavu-sans-fonts', 'diffutils']
    return []


def installed_module_file(name, files, suffix):
    """Resolve a unique absolute file from an installed RPM inventory."""
    candidates = [Path(path) for path in files.splitlines() if path.endswith(suffix)]
    if len(candidates) != 1 or not candidates[0].is_absolute() or '..' in candidates[0].parts:
        raise ValueError('Expected one installed ' + name + ' file')
    return candidates[0]


def module_commands(name, phase, directory, binary=None, driver=None, installed_files=''):
    """Fixed commands only; manifests select reviewed suites, never shell text."""
    if name not in MODULE_FIXTURES or phase not in ('runtime', 'sdk'):
        raise ValueError('Unknown module suite or phase')
    if name == 'ncurses':
        commands = [('tests', ['env', 'QORE_RPM_TEST_TMP=' + str(directory / 'runtime-fixture'),
                               str(directory / 'rpm/tests-installed/runtime')])]
        if phase == 'sdk':
            commands.append(('compiler', [str(directory / 'debian/tests/compiler')]))
        return commands
    if name in SIMPLE_MODULES:
        commands = []
        preloads = []
        for suffix in MODULE_PRELOADS.get(name, ()):
            preloads.extend(['-l', str(installed_module_file(name, installed_files, suffix))])
        for path in sorted(MODULE_FIXTURES[name]):
            if not path.endswith('.qtest'):
                continue
            command = ['qore', '-b', '--enable-debug', *preloads, str(directory / path), '-v']
            if name == 'sqlite3':
                command.extend(['--db', str(directory / 'qualification.sqlite')])
            if name == 'tar' and path == 'test/qtar.qtest':
                command = ['env', 'QORE_QTAR_BINARY=/usr/bin/qtar', 'QORE_MODULE_DIR=', *command]
            commands.append((Path(path).stem, command))
        if name == 'zip':
            commands.extend([
                ('features', ['qore', '-b', '--enable-debug',
                              str(directory / 'debian/tests/features'), '-v']),
                ('cli', ['/bin/sh', str(directory / 'debian/tests/cli'), '/usr/bin/qzip']),
            ])
        if name in ('cairo', 'imagemagick'):
            variable, binary = ('QORE_QSVG_BINARY', '/usr/bin/qsvg') if name == 'cairo' else (
                'QORE_QIMAGE_BINARY', '/usr/bin/qimage')
            commands.append(('cli', ['env', variable + '=' + binary,
                                     '/bin/sh', str(directory / 'debian/tests/cli')]))
        if phase == 'sdk':
            if name == 'markdown':
                compiled = directory / 'markdown-compiled'
                commands.extend([
                    ('compiler', ['qcc', '-o', str(compiled), str(directory / 'rpm/compiler.qr')]),
                    ('compiled-tests', [str(compiled)]),
                ])
            else:
                commands.append(('compiler', [str(directory / 'debian/tests/compiler')]))
        return commands
    if name == 'odbc':
        commands = [('tests', ['env', 'QORE_RPM_TEST_TMP=' + str(directory / 'runtime-fixture'),
                               str(directory / 'rpm/tests-installed-runtime')])]
        if phase == 'sdk':
            if binary is None or not binary.is_absolute() or binary.suffix != '.qmod':
                raise ValueError('ODBC SDK checks require the installed module path')
            if driver is None or not driver.is_absolute() or driver.name != 'psqlodbcw.so':
                raise ValueError('ODBC SDK checks require the installed PostgreSQL driver')
            compiled = directory / 'array-binding-compiled'
            commands.extend([
                ('native', ['env', 'QORE_ODBC_BINARY_MODULE=' + str(binary),
                            str(directory / 'rpm/test-postgres'), str(directory / 'test'), '--native']),
                ('compiler', ['qcc', '-o', str(compiled), str(directory / 'test/array-binding.qtest')]),
                ('compiled-tests', ['python3', '-B', str(directory / 'rpm/with-postgres.py'),
                                    '--driver', str(driver), '--', str(compiled), '-v']),
            ])
        return commands
    test_name = 'uuid-test.qtest' if name == 'uuid' else 'process.qtest'
    commands = [('tests', ['qore', '-b', '--enable-debug',
                           str(directory / 'test' / test_name), '-v'])]
    if phase == 'sdk':
        commands.append(('compiler', [str(directory / 'debian/tests/compiler')]))
        if name == 'process':
            if binary is None or not binary.is_absolute() or binary.suffix != '.qmod':
                raise ValueError('Process SDK checks require the installed module path')
            commands.append(('state', ['python3', '-B', '-W', 'error',
                str(directory / 'test/run-process-state.py'), '--module', str(binary)]))
    return commands


def install_command(family, paths):
    if family == 'suse':
        return ['zypper', '--non-interactive', 'install', '--no-recommends', *map(str, paths)]
    return ['dnf', '-y', '--setopt=gpgcheck=True', '--setopt=localpkg_gpgcheck=True',
            '--setopt=install_weak_deps=False', 'install', *map(str, paths)]


def installation_environment(family, directory, config=Path('/etc/zypp/zypp.conf')):
    """Install complete package payloads in Leap's otherwise doc-stripped image."""
    environment = os.environ.copy()
    if family == 'suse':
        text = config.read_text()
        setting = r'(?m)^\s*rpm\.install\.excludedocs\s*=.*$'
        text = re.sub(setting, 'rpm.install.excludedocs = no', text)
        if not re.search(setting, text):
            text += '\nrpm.install.excludedocs = no\n'
        target = directory / 'zypp.conf'
        target.write_text(text)
        environment['ZYPP_CONF'] = str(target)
    return environment


def require_rpm_signature(output):
    # rpmkeys also succeeds on unsigned RPMs whose digests are intact.
    if not re.search(r'(?m)^\s*(?:Header |Legacy )?(?:OpenPGP )?V\d+ [A-Za-z0-9/-]+ '
                     r'[Ss]ignature, key (?:ID [0-9a-f]{8,16}|fingerprint: [0-9a-f]{40,64}): OK$', output):
        raise ValueError('RPM has no verified signature')


def check_prerequisites(family):
    commands = ['rpm', 'rpmkeys', 'useradd', 'runuser', 'chown', 'zypper' if family == 'suse' else 'dnf']
    missing = [name for name in commands if shutil.which(name) is None]
    if missing:
        raise ValueError('Missing qualification fixture commands: ' + ', '.join(missing))


def run_logged(command, path, cwd=None, env=None, owner=None):
    """Stream fixture output through a pipe owned by its unprivileged writer.

    A fixture may save and restore stdout using /proc/self/fd. Giving it a
    root-owned regular log prevents reopening that descriptor; a writable
    regular file instead permits independent offsets to overwrite earlier
    output. An owned pipe supports descriptor reopening and preserves every
    byte in the parent-owned log without buffering the whole suite in memory.
    """
    with path.open('wb') as log:
        if owner is None:
            return subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, cwd=cwd, env=env)
        read_fd, write_fd = os.pipe()
        try:
            os.fchown(write_fd, *owner)
            with os.fdopen(read_fd, 'rb') as reader:
                read_fd = None
                with os.fdopen(write_fd, 'wb') as writer:
                    write_fd = None
                    with subprocess.Popen(command, stdout=writer, stderr=subprocess.STDOUT,
                                          cwd=cwd, env=env) as process:
                        writer.close()
                        try:
                            shutil.copyfileobj(reader, log)
                        except BaseException:
                            process.kill()
                            raise
                        return subprocess.CompletedProcess(command, process.wait())
        finally:
            if read_fd is not None:
                os.close(read_fd)
            if write_fd is not None:
                os.close(write_fd)


def qualify(manifest, output):
    validate(manifest)
    if platform.machine() != manifest['arch']:
        raise ValueError('Qualification requires a matching native runner')
    if os.geteuid() != 0:
        raise ValueError('Use a disposable root container for package installation')
    check_prerequisites(manifest['family'])
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    result = {'manifest': manifest, 'machine': platform.machine(),
              'runner_arch': os.environ.get('CI_RUNNER_EXECUTABLE_ARCH'), 'steps': []}

    def run(name, command, cwd=None, env=None, fixture=False):
        owner = pwd.getpwnam('qoretester') if fixture else None
        process = run_logged(command, output / (name + '.log'), cwd=cwd, env=env,
                             owner=(owner.pw_uid, owner.pw_gid) if owner else None)
        result['steps'].append({'name': name, 'command': command, 'exit_code': process.returncode})
        print(name, process.returncode, flush=True)
        process.check_returncode()
        return (output / (name + '.log')).read_text()

    try:
        # Verify all downloads before changing the container's package set.
        with tempfile.TemporaryDirectory(prefix='qore-rpm-native-') as temporary:
            root = Path(temporary)
            root.chmod(0o755)
            key = root / 'rpm-signing-key.asc'
            fetch_source(manifest['signing_key']['url'], manifest['signing_key']['sha256'], key)
            rpms = root / 'rpms'
            rpms.mkdir()
            source = root / 'source'
            for entry in manifest['packages']:
                fetch_source(entry['url'], entry['sha256'], rpms / entry['filename'])
            for entry in manifest['fixtures']:
                path = source / entry['path']
                fetch_source(entry['url'], entry['sha256'], path)
                path.chmod(0o755 if entry['path'].startswith('rpm/') else 0o644)
            for entry in manifest.get('modules', []):
                for fixture in entry['fixtures']:
                    path = source / ('module-' + entry['name']) / fixture['path']
                    fetch_source(fixture['url'], fixture['sha256'], path)
                    path.chmod(0o755 if path.suffix in ('.q', '.qtest', '.py')
                               or fixture['path'].startswith('rpm/')
                               or fixture['path'] == 'debian/tests/compiler' else 0o644)
            install_env = installation_environment(manifest['family'], root)
            run('import-signing-key', ['rpm', '--import', str(key)])
            for entry in manifest['packages']:
                signature = run('verify-signature-' + entry['name'],
                    ['rpmkeys', '--checksig', '--verbose', str(rpms / entry['filename'])],
                    env={**os.environ, 'LC_ALL': 'C'})
                require_rpm_signature(signature)
            run('create-user', ['useradd', '-M', '-U', 'qoretester'])
            for name in ('qore', 'qore-devel', 'gcc', 'gcc-c++'):
                probe = subprocess.run(['rpm', '-q', name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if probe.returncode != 1:
                    raise ValueError('Container is not a clean minimal runtime: ' + name)
            for phase in ('runtime', 'sdk'):
                entries = [entry for entry in manifest['packages'] if entry['phase'] == phase]
                paths = [rpms / entry['filename'] for entry in entries]
                if phase == 'sdk':
                    # cmake is a fixture tool, not a runtime requirement.
                    paths.append('cmake')
                for entry in manifest.get('modules', []):
                    paths.extend(module_dependencies(entry['name'], phase, manifest['family']))
                run(phase + '-install', install_command(manifest['family'], paths), env=install_env)
                names = [entry['name'] for entry in entries]
                run(phase + '-rpm-verify', ['rpm', '-V', *names])
                run(phase + '-inventory', ['rpm', '-qa', '--qf', '%{NAME} %{VERSION}-%{RELEASE}.%{ARCH}\n'])
                if phase == 'runtime':
                    for name in ('qore-devel', 'gcc', 'gcc-c++', 'unixODBC-devel'):
                        if subprocess.run(['rpm', '-q', name], stdout=subprocess.DEVNULL).returncode != 1:
                            raise ValueError('Runtime unexpectedly installed the compiler: ' + name)
                suites = ('runtime',) if phase == 'runtime' else ('runtime', 'development', 'tools', 'remote-debuggers')
                for suite in suites:
                    directory = root / (phase + '-' + suite)
                    directory.mkdir()
                    subprocess.run(['chown', 'qoretester:qoretester', str(directory)], check=True)
                    run(phase + '-' + suite, ['runuser', '-u', 'qoretester', '--', 'env',
                        'QORE_RPM_TEST_TMP=' + str(directory), str(source / 'rpm/tests-installed' / suite)],
                        fixture=True)
                for entry in manifest.get('modules', []):
                    name = entry['name']
                    directory = root / (phase + '-' + name)
                    shutil.copytree(source / ('module-' + name), directory)
                    subprocess.run(['chown', '-R', 'qoretester:qoretester', str(directory)], check=True)
                    binary = None
                    driver = None
                    files = ''
                    if name in MODULE_PRELOADS:
                        files = subprocess.check_output(['rpm', '-ql', 'qore-' + name + '-module'], text=True)
                    if phase == 'sdk' and name in ('process', 'odbc'):
                        files = subprocess.check_output(['rpm', '-ql', 'qore-' + name + '-module'], text=True)
                        binary = installed_module_file(name, files, '.qmod')
                    if phase == 'sdk' and name == 'odbc':
                        driver_package = 'psqlODBC' if manifest['family'] == 'suse' else 'postgresql-odbc'
                        files = subprocess.check_output(['rpm', '-ql', driver_package], text=True)
                        driver = installed_module_file('PostgreSQL ODBC driver', files, '/psqlodbcw.so')
                    environment = ['runuser', '-u', 'qoretester', '--', 'env']
                    for variable in ('QORE_MODULE_DIR', 'QORE_MODULE_DIR_ONLY', 'QORE_INCLUDE_DIR',
                                     'LD_LIBRARY_PATH', 'LD_PRELOAD'):
                        environment.extend(['-u', variable])
                    environment.append('AUTOPKGTEST_TMP=' + str(directory))
                    for suite, command in module_commands(name, phase, directory, binary, driver, files):
                        run(phase + '-' + name + '-' + suite, environment + command,
                            cwd=directory, fixture=True)
        result['exit_code'] = 0
    except BaseException as error:
        result.update(exit_code=1, error=repr(error))
        raise
    finally:
        (output / 'qualification.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    qualify(json.loads(args.manifest.read_text()), args.output)


if __name__ == '__main__':
    main()
