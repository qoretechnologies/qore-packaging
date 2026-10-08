# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import runpy
import shutil

root = Path(__file__).resolve().parent.parent
source = root / 'results/core21-removal-final2-20261008'
out = root / 'evidence/controls/core21-removal-20261008'
out.mkdir()
status = json.loads((source / 'status.json').read_text())
assert all(v['exit_code'] == 0 for v in status.values()) and len(status) == 3
results = {}
for target in ('fedora', 'leap', 'el10'):
    record = json.loads((source / target / 'qualification.json').read_text())
    assert record['exit_code'] == 0
    assert all(s['exit_code'] == s['expected_exit_code'] for s in record['steps'])
    names = {s['name'] for s in record['steps']}
    assert {'reject-library-removal', 'remove-original-core', 'signed-install-dry-run',
            'signed-install', 'verify-signed-core', 'reinstalled-runtime', 'reinstalled-development',
            'remove-signed-core', 'reinstall-signed-core', 'verify-reinstalled-core', 'reinstalled-load'} <= names
    assert record['original_payload_files'] > 100 and record['signed_payload_files'] > 100
    expected = json.loads((root / f'results/core21-upgrade-baseline-20261008/{target}-x86_64/manifest.json').read_text())
    assert record['source_manifest'] == expected
    for step in record['steps']:
        text = (source / target / (step['name'] + '.log')).read_text()
        if step['name'] != 'reject-library-removal':
            unexpected = [line for line in text.splitlines()
                          if re.search(r'\bwarning:|CMake (?:Warning|Error)|^error:', line, re.I)]
            assert not unexpected, (target, step['name'], unexpected)
    results[target] = {'image': status[target]['image'], 'steps': len(record['steps']),
                       'core_packages': record['core_packages'],
                       'original_payload_files': record['original_payload_files'],
                       'signed_payload_files': record['signed_payload_files'],
                       'negative_dependency_check': 'RPM rejects removal of libqore while consumers are installed, without changing the package inventory.',
                       'runtime': 'Installed runtime suites including ONNX inference pass after signed installation.',
                       'sdk': 'Installed C++ embedding, CMake discovery, AOT program/module and metadata/compiler suites pass.',
                       'removal': 'All recorded core files/symlinks disappear, qore/qcc disappear, and no other package is erased.',
                       'reinstall': 'The package inventory is restored exactly, rpm -V passes, and ML retains ONNX support.'}
for path in sorted(source.rglob('*')):
    if not path.is_file():
        continue
    dest = out / path.relative_to(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix in ('.log', '.txt'):
        dest.with_suffix(dest.suffix + '.gz').write_bytes(gzip.compress(path.read_bytes(), mtime=0))
    else:
        shutil.copyfile(path, dest)
for attempt in ('core21-removal-20261008', 'core21-removal-final-20261008'):
    for target in ('fedora', 'leap', 'el10'):
        directory = root / 'results' / attempt / target
        dest = out / 'fixture-corrections' / attempt / target
        dest.mkdir(parents=True)
        for name in ('driver.log', 'signed-install-dry-run.log', 'qualification.json'):
            path = directory / name
            if path.exists():
                (dest / (name + '.gz')).write_bytes(gzip.compress(path.read_bytes(), mtime=0))
for name in ('check-core21-removal-20261008.py', 'run-core21-removal-20261008.py', 'record-core21-removal-20261008.py'):
    shutil.copyfile(root / 'work' / name, out / name)
tests = root / 'results/core21-lifecycle-catalog-tests-20261008.log'
assert tests.read_text().rstrip().endswith('OK')
(out / (tests.name + '.gz')).write_bytes(gzip.compress(tests.read_bytes(), mtime=0))
audit = runpy.run_path(str(root / 'work/write-scoped-audit.py'))
audit['write'](out / 'audit.rst', 'Core21 removal and reinstall evidence audit',
    'Scope: disposable offline x86_64 RPM core transaction checks and catalog correction. '
    'All 62 checks reviewed: ten Pass, 52 N/A. Actual transactions and installed runtime/SDK suites pass on all three distributions.',
    {9: 'New scripts and evidence use copyright 2026; raw outputs are preserved.',
     53: 'No dependency bypass, signature bypass or warning suppression. Results explicitly exclude clean solver installs, new-version upgrades and ARM.',
     54: 'Containers are disposable; all commands check exact expected results; failures record incomplete status and cannot be accepted.',
     55: 'Each parallel worker owns a distinct container and output directory.',
     56: 'Known manifest schema, architecture, source revision, seven core package names and SHA-256/signature pins are checked.',
     57: 'Existing qualified SDK images and cached RPMs are reused; no builds or image snapshots are created.',
     58: 'Negative dependency test checks the reason and unchanged inventory; dry run rejects inconsistent dependency releases. Final fixture preserves the existing matched SDK dependency pairs.',
     59: 'Evidence describes commands, initial fixture failures, package identities, runtime/SDK coverage and exclusions.',
     61: 'Root actions require a Docker container, mounted inputs are read-only, network is disabled, and all package bytes and signatures are verified.',
     62: 'All three actual transaction sequences pass; removal checks every recorded non-directory payload path; reinstall restores the exact signed inventory. No runtime C++ implementation changes.'},
    'No Qore/C++/QPP/module/DataProvider/JNI implementation changed in this fixture/evidence scope.')
record = {'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
          'status': 'Signed core21 removal/reinstall checks and installed runtime/SDK tests pass on Fedora, Leap and AlmaLinux x86_64.',
          'source_commit': 'd58eec0b2ab721ef5da0e2136c4cddb3579874e2', 'targets': results,
          'fixture_corrections': [
              'First launch stopped before package mutation because the mounted helper lacked qualification/jni-fixtures.json. The final launcher mounts the required public metadata read-only.',
              'First signed-install dry run rejected attempts to replace dependency runtime RPMs while retaining local development RPMs with exact-release requirements. The final gate installs only the seven core RPMs and preserves the SDK dependency pairs; dependency checks remain enabled.'],
          'catalog_correction': 'MySQL ARM runtime/SDK checks already passed pipeline 59974/59977; catalog status now points to database-native-installed-20261008.json instead of marking that gate pending.',
          'limits': ['This is an offline RPM transaction check using previously qualified SDK images, not a fresh repository solver install.',
                     'It does not qualify cross-version upgrades, module co-installation/removal, native ARM removal or signed repository metadata.',
                     'The separate six-target frozen baseline provides inputs for later cross-version testing. Publication remains disabled.'],
          'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(out.rglob('*')) if p.is_file()}}
(root / 'evidence/core21-removal-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS: all three signed core removal/reinstall sequences; installed runtime/SDK tests; complete audit')
