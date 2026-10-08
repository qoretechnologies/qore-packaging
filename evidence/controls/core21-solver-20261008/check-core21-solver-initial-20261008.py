# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Test signed repository discovery and installation by package name in a clean container."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import pwd
import re
import shutil
import subprocess
import sys

sys.path.insert(0, '/tools')
spec = importlib.util.spec_from_file_location('installed', '/tools/qualify-installed.py')
installed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installed)
out = Path('/results')
steps = []


def run(name, command, env=None, reject=False):
    result = subprocess.run(command, capture_output=True, text=True, env=env)
    text = result.stdout + result.stderr
    (out / (name + '.log')).write_text(text)
    steps.append({'name': name, 'command': command, 'exit_code': result.returncode, 'negative_control': reject})
    print(name, result.returncode, flush=True)
    if reject:
        if result.returncode == 0 or not re.search(r'(?i)(bad.*signature|signature.*(fail|invalid)|gpg.*(error|fail))', text):
            raise ValueError('Package manager did not reject the invalid metadata signature')
    else:
        result.check_returncode()
    return text


def main():
    if not Path('/.dockerenv').exists() or os.getuid() != 0:
        raise ValueError('Requires a disposable root Docker container')
    manifest = installed.validate(json.loads(Path('/manifest.json').read_text()))
    family = manifest['family']
    expected_key = json.loads(Path('/repository-status.json').read_text())['metadata_public_key_sha256']
    for key, expected in [('metadata-public-key.asc', expected_key),
                          ('package-public-key.asc', manifest['signing_key']['sha256'])]:
        if hashlib.sha256((Path('/repository') / key).read_bytes()).hexdigest() != expected:
            raise ValueError('Signing key bytes changed')
        run('import-' + key, ['rpm', '--import', '/repository/' + key])
    for name in ('qore', 'qore-devel', 'gcc', 'gcc-c++'):
        if subprocess.run(['rpm', '-q', name], capture_output=True).returncode != 1:
            raise ValueError('Container already has ' + name)
    for entry in manifest['packages']:
        rpm = Path('/repository/Packages') / entry['filename']
        with rpm.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != entry['sha256']:
                raise ValueError('Changed RPM payload')
        installed.require_rpm_signature(run('signature-' + entry['name'], ['rpmkeys', '--checksig', '--verbose', str(rpm)]))
    repo_dir = Path('/etc/zypp/repos.d' if family == 'suse' else '/etc/yum.repos.d')
    text = ('[{name}]\nname=Qore local qualification\nbaseurl=file://{path}\nenabled=1\n'
            'gpgcheck=1\nrepo_gpgcheck=1\npkg_gpgcheck=1\nskip_if_unavailable=0\n'
            'gpgkey=file:///repository/metadata-public-key.asc file:///repository/package-public-key.asc\n')
    (repo_dir / 'qore-local-qualification.repo').write_text(text.format(name='qore-local-qualification', path='/repository'))
    bad = Path('/tmp/qore-bad-repository/repodata')
    bad.mkdir(parents=True)
    for filename in ('repomd.xml', 'repomd.xml.asc', 'repomd.xml.key'):
        shutil.copyfile(Path('/repository/repodata') / filename, bad / filename)
    with (bad / 'repomd.xml').open('ab') as stream:
        stream.write(b'\n<!-- invalid signature negative control -->\n')
    bad_config = repo_dir / 'qore-bad-qualification.repo'
    bad_config.write_text(text.format(name='qore-bad-qualification', path='/tmp/qore-bad-repository'))
    env = installed.installation_environment(family, out)
    if family == 'suse':
        refresh = ['zypper', '--non-interactive', 'refresh', '--force', 'qore-local-qualification']
        bad_refresh = ['zypper', '--non-interactive', 'refresh', '--force', 'qore-bad-qualification']
    else:
        common = ['dnf', '-y', '--disablerepo=*']
        refresh = [*common, '--enablerepo=qore-local-qualification', 'makecache', '--refresh']
        bad_refresh = [*common, '--enablerepo=qore-bad-qualification', 'makecache', '--refresh']
    run('reject-tampered-metadata', bad_refresh, env, reject=True)
    bad_config.unlink()
    run('signed-repository-refresh', refresh, env)
    run('create-fixture-user', ['useradd', '-r', '-M', '-U', 'qoretester'])
    account = pwd.getpwnam('qoretester')
    core = [entry for entry in manifest['packages'] if entry['url'].split('/')[-2] == 'qore']
    for phase in ('runtime', 'sdk'):
        requests = ['qore'] if phase == 'runtime' else [e['name'] for e in core if e['phase'] == 'sdk'] + ['cmake']
        run(phase + '-install-by-name', installed.install_command(family, requests), env)
        names = [e['name'] for e in core if e['phase'] == phase]
        for entry in [e for e in core if e['phase'] == phase]:
            fmt = '%{NAME} %{VERSION}-%{RELEASE}.%{ARCH}\n'
            expected = subprocess.check_output(['rpm', '-qp', '--qf', fmt, '/repository/Packages/' + entry['filename']], text=True)
            actual = subprocess.check_output(['rpm', '-q', '--qf', fmt, entry['name']], text=True)
            if actual != expected:
                raise ValueError('Solver selected an unexpected build of ' + entry['name'])
        run(phase + '-rpm-verify', ['rpm', '-V', *names])
        run(phase + '-inventory', ['rpm', '-qa', '--qf', '%{NAME} %{VERSION}-%{RELEASE}.%{ARCH}\n'])
        if phase == 'runtime':
            for name in ('qore-devel', 'gcc', 'gcc-c++'):
                if subprocess.run(['rpm', '-q', name], capture_output=True).returncode != 1:
                    raise ValueError('Runtime pulled in compiler package ' + name)
        for suite in ('runtime',) if phase == 'runtime' else ('runtime', 'development', 'tools', 'remote-debuggers'):
            work = Path('/tmp') / (phase + '-' + suite)
            work.mkdir()
            os.chown(work, account.pw_uid, account.pw_gid)
            run(phase + '-' + suite, ['runuser', '-u', 'qoretester', '--', 'env',
                'QORE_RPM_TEST_TMP=' + str(work), 'sh', '/fixtures/rpm/tests-installed/' + suite])
    return {'manifest': manifest, 'scope': 'Clean x86_64 repository discovery and dependency-solving installation by package name; signed metadata uses an ephemeral local key and packages retain OBS signatures.'}


result = {'exit_code': 1}
try:
    result.update(main(), exit_code=0)
except BaseException as error:
    result['error'] = repr(error)
    raise
finally:
    result['steps'] = steps
    (out / 'qualification.json').write_text(json.dumps(result, indent=2) + '\n')
