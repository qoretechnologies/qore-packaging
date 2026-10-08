# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import runpy
import shutil
import xml.etree.ElementTree as ET

root = Path.cwd()
out = root / 'evidence/controls/database-native-installed-20261008'
out.mkdir()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
records = {}
for target, job in [('fedora', 209696), ('leap', 209697)]:
    base = root / f'results/database-installed-native-20261008/{target}/results/native-installed'
    result = json.loads((base / 'qualification.json').read_text())
    assert result['machine'] == 'aarch64' and result['exit_code'] == 0
    assert all(s['exit_code'] == 0 for s in result['steps'])
    assert result['manifest'] == json.loads((root / f'qualification/databases-{target}-aarch64.json').read_text())
    counts = {}
    for phase in ['runtime', 'sdk']:
        counts[phase] = {}
        for module, expected in [('freetds', (4, 14)), ('mysql', (34, 203))]:
            p = base / (phase + '-' + module + '-tests.log')
            cases = [tuple(map(int, m)) for m in re.findall(r'Ran (\d+) test cases, (\d+) succeeded \((\d+) assertions\)', p.read_text())]
            assert all(c[0] == c[1] for c in cases)
            assert (sum(c[0] for c in cases), sum(c[2] for c in cases)) == expected
            counts[phase][module] = {'cases': expected[0], 'assertions': expected[1]}
    records[target] = {'pipeline': 59974, 'job': job, 'steps': len(result['steps']), 'phases': counts,
                       'signature_verification': 'All pinned RPM signatures passed before installation.',
                       'core_sdk': 'Runtime/ONNX, SDK compiler, utility and remote debugger checks all pass.'}
    for p in sorted(base.rglob('*')):
        if not p.is_file() or p.suffix == '.rpm':
            continue
        dest = out / target / p.relative_to(base)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix == '.log':
            dest.with_suffix('.log.gz').write_bytes(gzip.compress(p.read_bytes(), mtime=0))
        else:
            shutil.copyfile(p, dest)

source = root / 'results/el10-installed-refreshed-inputs-20261008'
sources = json.loads((source / 'sources.json').read_text())
for data in sources.values():
    folder = source / data['source_package']
    for p in data['packages'].values():
        assert sha(folder / p['filename']) == p['sha256']
for p in sorted(source.rglob('*')):
    if p.is_file() and p.suffix != '.rpm':
        dest = out / 'el10-refreshed-inputs' / p.relative_to(source)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dest)
unit = root / 'results/el10-manifest-refresh-tests-20261008.log'
assert 'Ran 227 tests' in unit.read_text() and unit.read_text().rstrip().endswith('OK')
(out / 'unit-tests.log.gz').write_bytes(gzip.compress(unit.read_bytes(), mtime=0))
for name in ['refresh-el10-installed-inputs-20261008.py', 'download-database-installed-20261008.py', 'record-database-native-installed-20261008.py']:
    shutil.copyfile(root / 'work' / name, out / name)

audit = runpy.run_path(str(root / 'work/write-scoped-audit.py'))
passes = {
    9: 'New audit, evidence and verification scripts carry Copyright 2026.',
    53: 'Stale artifact filenames/hashes are replaced by downloaded OBS binaries; no retry, skip, package behavior or verification policy changes.',
    59: 'The evidence records both successful ARM installations, the failed AlmaLinux download, its cause, and the pending rerun. Initial preparer confusion between RPM and fixture-only commits is corrected without changing fixture pins.',
    61: 'All replacement artifacts were downloaded and hashed; core source srcmd5 is unchanged. Signature and fixture validation remain enabled. No secrets are added.',
    62: 'All 227 packaging tests pass. Fedora and Leap pass every runtime/SDK step. Every refreshed AlmaLinux RPM and immutable fixture was downloaded and validated before committing; the new native rerun remains required.'
}
audit['write'](root / 'audits/database-native-input-refresh-20261008.rst', 'Database native input refresh audit',
               'Scope: two AlmaLinux artifact manifests and native verification evidence. All 62 checklist entries reviewed: 5 Pass, 57 N/A, 0 Fail. No production or runner code changed.',
               passes, 'No corresponding C++, Qore/QPP module, DataProvider, JNI, concurrency or production runtime change in this artifact-pin-only scope.')
paths = ['qualification/core21-el10-aarch64.json', 'qualification/databases-el10-aarch64.json',
         'audits/database-native-input-refresh-20261008.rst']
evidence = {
    'schema': 1, 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.', 'date': '2026-10-08',
    'result': 'Fedora and Leap signed native ARM database runtime/SDK qualification pass. AlmaLinux artifact pins are corrected and ready for the required native rerun.',
    'targets': records,
    'el10_initial_failure': {'pipeline': 59974, 'job': 209698, 'before_installation': True,
        'error': 'HTTP 404 for libqore-3.0.0~git20261003.21-21.1.aarch64.rpm',
        'root_cause': 'The original core21 template retained build counter 1; OBS replaced these outputs after dependency rebuilds with counter 3 (and corresponding dependency counters).',
        'fix': 'Refresh all core/dependency artifact pins from the successful current native builds, retaining core source srcmd5 ba3b6bc9ac8055ee991e334102e7ad16. Download/hash every referenced RPM before rerunning.'},
    'preparation_correction': 'An initial optional PostgreSQL refresh incorrectly substituted its packaged commit for the later fixture-only commit, causing an HTTP 404. The corrected preparer preserves the previously qualified fixture commit, verifies its bytes and leaves the PostgreSQL manifest byte-identical. All downloaded RPMs were retained and rehashed.',
    'el10_sources': sources,
    'tests': {'packaging': 227, 'audit_pass': 5, 'audit_na': 57, 'audit_fail': 0},
    'diagnostics': 'Only the previously approved deliberate MySQL negative-authentication message appears in the successful native module suites. No new warning acceptance or suppression.',
    'publication': 'disabled',
    'pending': 'AlmaLinux native installed rerun; repository lifecycle, latest core/module source qualification and publication gates.',
    'qualified_files_sha256': {p: sha(root / p) for p in paths},
    'files_sha256': {str(p.relative_to(root)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
}
(root / 'evidence/database-native-installed-20261008.json').write_text(json.dumps(evidence, indent=2) + '\n')
print('PASS: two signed native targets archived; AlmaLinux pins validated; all 62 audit checks complete')
