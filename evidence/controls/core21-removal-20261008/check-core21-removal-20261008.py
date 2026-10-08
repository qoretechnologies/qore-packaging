# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Exercise exact signed core RPM removal/reinstall in a disposable SDK container."""
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import pwd
import shutil
import stat
import subprocess
import sys

sys.path.insert(0, '/tools')
spec = importlib.util.spec_from_file_location('installed', '/tools/qualify-installed.py')
installed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installed)
OUT = Path('/results')
CACHE = Path('/baseline')
steps = []


def run(name, command, expected=0, **kwargs):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, env={**os.environ, 'LC_ALL': 'C'}, **kwargs)
    (OUT / (name + '.log')).write_text(result.stdout)
    steps.append({'name': name, 'command': command, 'exit_code': result.returncode,
                  'expected_exit_code': expected})
    if result.returncode != expected:
        raise ValueError(f'{name}: unexpected exit {result.returncode}, expected {expected}')
    return result.stdout


def inventory():
    return subprocess.check_output(['rpm', '-qa', '--qf', '%{NAME}\t%{VERSION}-%{RELEASE}.%{ARCH}\n'], text=True)


def files(names):
    text = subprocess.check_output(['rpm', '-q', '--qf', '[%{FILENAMES}\t%{FILEMODES}\n]', *names], text=True)
    return sorted({p for line in text.splitlines() for p, mode in [line.rsplit('\t', 1)]
                   if not stat.S_ISDIR(int(mode))})


def absent(names, payload):
    current = {line.split('\t')[0] for line in inventory().splitlines()}
    if set(names) & current:
        raise ValueError('Core packages remain installed')
    leftovers = [p for p in payload if os.path.lexists(p)]
    if leftovers:
        raise ValueError('Core payload survives removal: ' + repr(leftovers))
    if shutil.which('qore') or shutil.which('qcc'):
        raise ValueError('Qore executable survives removal')


def main():
    if not Path('/.dockerenv').is_file() or os.getuid() != 0:
        raise ValueError('This destructive fixture requires a disposable root Docker container')
    manifest = installed.validate(json.loads(Path('/manifest.json').read_text()))
    if manifest['arch'] != 'x86_64' or manifest['obs_srcmd5'] != 'ba3b6bc9ac8055ee991e334102e7ad16':
        raise ValueError('Unexpected baseline identity')
    core = [e for e in manifest['packages'] if e['url'].split('/')[-2] == 'qore']
    names = sorted(e['name'] for e in core)
    if len(names) != 7:
        raise ValueError('Expected the seven core runtime/SDK packages')
    for entry in manifest['packages']:
        with (CACHE / entry['filename']).open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != entry['sha256']:
                raise ValueError('Changed baseline package')
    if hashlib.sha256((CACHE / 'key.asc').read_bytes()).hexdigest() != manifest['signing_key']['sha256']:
        raise ValueError('Changed signing key')
    run('import-key', ['rpm', '--import', str(CACHE / 'key.asc')])
    for entry in manifest['packages']:
        installed.require_rpm_signature(run('signature-' + entry['name'],
            ['rpmkeys', '--checksig', '--verbose', str(CACHE / entry['filename'])]))
    initial = inventory()
    (OUT / 'initial-inventory.txt').write_text(initial)
    library = 'libqore20' if manifest['family'] == 'suse' else 'libqore'
    negative = run('reject-library-removal', ['rpm', '-e', '--test', library], expected=1)
    if 'is needed by (installed)' not in negative or 'qore-' not in negative:
        raise ValueError('Expected RPM dependency rejection')
    if inventory() != initial:
        raise ValueError('Rejected erase changed the RPM inventory')
    old_payload = files(names)
    run('remove-original-core', ['rpm', '-e', *names])
    absent(names, old_payload)
    # The existing SDK has matched dependency runtime/development releases.
    # Preserve those pairs while testing the seven signed core packages.
    install = ['rpm', '-Uvh', '--replacepkgs', *[str(CACHE / e['filename']) for e in core]]
    run('signed-install-dry-run', [*install[:2], '--test', *install[2:]])
    run('signed-install', install)
    run('verify-signed-core', ['rpm', '-V', *names])
    signed_payload = files(names)
    signed_inventory = inventory()
    (OUT / 'signed-inventory.txt').write_text(signed_inventory)
    try:
        account = pwd.getpwnam('qoretester')
    except KeyError:
        run('create-fixture-user', ['useradd', '-r', '-M', '-U', 'qoretester'])
        account = pwd.getpwnam('qoretester')
    for suite in ('runtime', 'development'):
        directory = Path('/tmp') / ('qore-reinstalled-' + suite)
        directory.mkdir()
        os.chown(directory, account.pw_uid, account.pw_gid)
        run('reinstalled-' + suite, ['runuser', '-u', 'qoretester', '--', 'env',
            'QORE_RPM_TEST_TMP=' + str(directory), 'sh', str(CACHE / 'fixtures/rpm/tests-installed' / suite)],
            cwd=directory)
    run('remove-signed-core', ['rpm', '-e', *names])
    absent(names, signed_payload)
    # Core removal must not erase any independently installed dependency.
    after = inventory()
    expected = sorted(line for line in signed_inventory.splitlines() if line.split('\t')[0] not in names)
    if sorted(after.splitlines()) != expected:
        raise ValueError('Core erase changed another package')
    (OUT / 'removed-inventory.txt').write_text(after)
    run('reinstall-signed-core', ['rpm', '-ivh', *[str(CACHE / e['filename']) for e in core]])
    run('verify-reinstalled-core', ['rpm', '-V', *names])
    if sorted(inventory().splitlines()) != sorted(signed_inventory.splitlines()):
        raise ValueError('Reinstall did not restore the package set')
    run('reinstalled-load', ['qore', '-b', '--enable-debug', '-l', 'ml', '-e',
                            'if (!ML::ml_get_capabilities().has_onnx) { exit(1); }'])
    return {'original_payload_files': len(old_payload), 'signed_payload_files': len(signed_payload),
            'core_packages': names, 'source_manifest': manifest,
            'scope': 'Offline RPM transactions in prior qualified SDK image; not a clean solver install, cross-version upgrade or ARM result.'}


if __name__ == '__main__':
    result = {'exit_code': 1}
    try:
        result.update(main(), exit_code=0)
    except BaseException as error:
        result['error'] = repr(error)
        raise
    finally:
        result['steps'] = steps
        (OUT / 'qualification.json').write_text(json.dumps(result, indent=2) + '\n')
