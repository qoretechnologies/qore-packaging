# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Removal/reinstall qualification after a clean signed core installation."""
import os
from pathlib import Path
import re
import shutil
import stat

import repository_fixture


INVENTORY_FORMAT = '%{NAME}\t%{EPOCHNUM}:%{VERSION}-%{RELEASE}.%{ARCH}\n'


def core_packages(manifest):
    """Limit erasure to the seven core packages installed by this fixture."""
    if manifest.get('modules'):
        raise ValueError('Core lifecycle requires a core-only qualification manifest')
    library = 'libqore20' if manifest['family'] == 'suse' else 'libqore'
    expected = {library, 'qore', 'qore-stdlib', 'qore-devel', 'qore-rpm-macros',
                'qore-misc-tools', 'qore-debug-tools'}
    entries = [entry for entry in manifest['packages'] if entry['url'].split('/')[-2] == 'qore']
    if len(entries) != 7 or {entry['name'] for entry in entries} != expected:
        raise ValueError('Core lifecycle requires exactly seven pinned core runtime/SDK packages')
    return sorted(entries, key=lambda entry: entry['name'])


def check_dependency_rejection(returncode, text, library):
    if library not in ('libqore', 'libqore20') or returncode != 1:
        raise ValueError('Expected the core library dependency rejection')
    if not re.search(r'^error: Failed dependencies:\s*$', text, re.M) or not re.search(
            r'^\s*' + library + r'(?:\([^\n]*\))?(?:\s+[^\n]*)? is needed by \(installed\) qore-', text, re.M):
        raise ValueError('Core library removal failed for an unexpected reason')


def inventory(text):
    lines = text.splitlines()
    if not lines or any(len(line.split('\t')) != 2 for line in lines) or len(lines) != len(set(lines)):
        raise ValueError('Malformed installed package inventory')
    return sorted(lines)


def payload_files(text):
    files = set()
    for line in text.splitlines():
        name, mode = line.rsplit('\t', 1)
        path = Path(name)
        if not path.is_absolute() or '..' in path.parts:
            raise ValueError('Unsafe RPM payload path')
        if not stat.S_ISDIR(int(mode)):
            files.add(name)
    if not files:
        raise ValueError('Core package payload is empty')
    return sorted(files)


def verify_removed(names, before, after, payload):
    expected = [line for line in before if line.split('\t')[0] not in names]
    if after != expected:
        raise ValueError('Core removal retained core packages or changed other packages')
    leftovers = [name for name in payload if os.path.lexists(name)]
    if leftovers or any(shutil.which(name) for name in ('qore', 'qcc')):
        raise ValueError('Core payload survives removal: ' + repr(leftovers))


def qualify(manifest, rpms, run, environment, install_command):
    """Use the runner's verified repository, preserving all unrelated packages."""
    packages = core_packages(manifest)
    names = [entry['name'] for entry in packages]
    library = 'libqore20' if manifest['family'] == 'suse' else 'libqore'
    before = inventory(run('lifecycle-before', ['rpm', '-qa', '--qf', INVENTORY_FORMAT]))
    installed_names = {line.split('\t')[0] for line in before}
    if not set(names) <= installed_names:
        raise ValueError('Core lifecycle requires the completed SDK installation')
    payload = payload_files(run('lifecycle-payload',
        ['rpm', '-q', '--qf', '[%{FILENAMES}\t%{FILEMODES}\n]', *names]))
    run('lifecycle-reject-library-removal', ['rpm', '-e', '--test', library],
        env=dict(environment, LC_ALL='C'), reject_dependency=library)
    unchanged = inventory(run('lifecycle-after-rejection', ['rpm', '-qa', '--qf', INVENTORY_FORMAT]))
    if unchanged != before:
        raise ValueError('Rejected erase changed installed packages')
    command = (['zypper', '--non-interactive', 'remove', *names] if manifest['family'] == 'suse' else
               ['dnf', '-y', '--setopt=clean_requirements_on_remove=False', 'remove', *names])
    run('lifecycle-remove', command, env=environment)
    after = inventory(run('lifecycle-removed-inventory', ['rpm', '-qa', '--qf', INVENTORY_FORMAT]))
    verify_removed(names, before, after, payload)
    reinstall = install_command(manifest['family'], names)
    if manifest['family'] == 'suse':
        reinstall.insert(reinstall.index('install') + 1, '--allow-vendor-change')
    run('lifecycle-reinstall', reinstall, env=environment)
    repository_fixture.verify_selected_versions(packages, rpms,
        lambda name, command: run('lifecycle-' + name, command))
    restored = inventory(run('lifecycle-restored-inventory', ['rpm', '-qa', '--qf', INVENTORY_FORMAT]))
    if restored != before:
        raise ValueError('Reinstall did not restore the exact package set')
    run('lifecycle-rpm-verify', ['rpm', '-V', *names])
    return {'core_packages': names, 'payload_files_checked': len(payload),
            'unrelated_packages_preserved': True, 'exact_inventory_restored': True,
            'scope': 'Same-version signed repository removal/reinstall; cross-version upgrade is a separate gate.'}
