#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Qualify pinned OBS RPMs in a disposable native distribution container."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import tempfile

from packaging import fetch_source

FIXTURES = {'rpm/tests-installed/' + name for name in ('runtime', 'development', 'tools', 'remote-debuggers')}
FIXTURES.add('modules/ml/test/data/test_linear.onnx')
MODULE_FIXTURES = {
    'uuid': {'test/uuid-test.qtest', 'debian/tests/compiler'},
    'process': {'test/process.qtest', 'test/process-state.qtest',
                'test/process-state-fixture.c', 'test/run-process-state.py',
                'debian/tests/compiler'} | {
                    'test/test_' + name + '.q' for name in
                    ('cwd', 'env', 'false', 'io', 'output', 'signal', 'sleep',
                     'stdin_eof', 'true', 'utf8')},
}


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


def module_commands(name, phase, directory, binary=None):
    """Fixed commands only; manifests select reviewed suites, never shell text."""
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

    def run(name, command, cwd=None, env=None):
        with (output / (name + '.log')).open('w') as log:
            process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, cwd=cwd, env=env)
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
                if any(entry['name'] == 'process' for entry in manifest.get('modules', [])):
                    paths.append('procps' if manifest['family'] == 'suse' else 'procps-ng')
                run(phase + '-install', install_command(manifest['family'], paths), env=install_env)
                names = [entry['name'] for entry in entries]
                run(phase + '-rpm-verify', ['rpm', '-V', *names])
                run(phase + '-inventory', ['rpm', '-qa', '--qf', '%{NAME} %{VERSION}-%{RELEASE}.%{ARCH}\n'])
                if phase == 'runtime':
                    for name in ('qore-devel', 'gcc', 'gcc-c++'):
                        if subprocess.run(['rpm', '-q', name], stdout=subprocess.DEVNULL).returncode != 1:
                            raise ValueError('Runtime unexpectedly installed the compiler: ' + name)
                suites = ('runtime',) if phase == 'runtime' else ('runtime', 'development', 'tools', 'remote-debuggers')
                for suite in suites:
                    directory = root / (phase + '-' + suite)
                    directory.mkdir()
                    subprocess.run(['chown', 'qoretester:qoretester', str(directory)], check=True)
                    run(phase + '-' + suite, ['runuser', '-u', 'qoretester', '--', 'env',
                        'QORE_RPM_TEST_TMP=' + str(directory), str(source / 'rpm/tests-installed' / suite)])
                for entry in manifest.get('modules', []):
                    name = entry['name']
                    directory = root / (phase + '-' + name)
                    shutil.copytree(source / ('module-' + name), directory)
                    subprocess.run(['chown', '-R', 'qoretester:qoretester', str(directory)], check=True)
                    binary = None
                    if phase == 'sdk' and name == 'process':
                        files = subprocess.check_output(['rpm', '-ql', 'qore-process-module'], text=True)
                        binaries = [Path(p) for p in files.splitlines() if p.endswith('.qmod')]
                        if len(binaries) != 1:
                            raise ValueError('Expected one installed process binary module')
                        binary = binaries[0]
                    environment = ['runuser', '-u', 'qoretester', '--', 'env']
                    for variable in ('QORE_MODULE_DIR', 'QORE_MODULE_DIR_ONLY', 'QORE_INCLUDE_DIR',
                                     'LD_LIBRARY_PATH', 'LD_PRELOAD'):
                        environment.extend(['-u', variable])
                    environment.append('AUTOPKGTEST_TMP=' + str(directory))
                    for suite, command in module_commands(name, phase, directory, binary):
                        run(phase + '-' + name + '-' + suite, environment + command, cwd=directory)
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
