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
    for entry in fixtures + manifest.get('packages', []):
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


def install_command(family, paths):
    if family == 'suse':
        return ['zypper', '--non-interactive', '--no-gpg-checks', 'install', '--no-recommends',
                '--allow-unsigned-rpm', *map(str, paths)]
    return ['dnf', '-y', '--nogpgcheck', '--setopt=install_weak_deps=False', 'install', *map(str, paths)]


def check_prerequisites(family):
    commands = ['rpm', 'useradd', 'runuser', 'chown', 'zypper' if family == 'suse' else 'dnf']
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

    def run(name, command):
        with (output / (name + '.log')).open('w') as log:
            process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        result['steps'].append({'name': name, 'command': command, 'exit_code': process.returncode})
        print(name, process.returncode, flush=True)
        process.check_returncode()

    try:
        # Verify all downloads before changing the container's package set.
        with tempfile.TemporaryDirectory(prefix='qore-rpm-native-') as temporary:
            root = Path(temporary)
            root.chmod(0o755)
            rpms = root / 'rpms'
            rpms.mkdir()
            source = root / 'source'
            for entry in manifest['packages']:
                fetch_source(entry['url'], entry['sha256'], rpms / entry['filename'])
            for entry in manifest['fixtures']:
                path = source / entry['path']
                fetch_source(entry['url'], entry['sha256'], path)
                path.chmod(0o755 if entry['path'].startswith('rpm/') else 0o644)
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
                run(phase + '-install', install_command(manifest['family'], paths))
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
