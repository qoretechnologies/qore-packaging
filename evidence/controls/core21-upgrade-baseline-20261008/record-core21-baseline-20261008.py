# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Archive reproducible baseline metadata without adding RPM binaries to Git."""
from pathlib import Path
import gzip
import hashlib
import json
import runpy
import shutil
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'work'))
freeze = runpy.run_path(str(ROOT / 'work/freeze-core21-baseline-20261008.py'))
sha = freeze['sha']
source = ROOT / 'results/core21-upgrade-baseline-20261008'
out = ROOT / 'evidence/controls/core21-upgrade-baseline-20261008'
out.mkdir()
results = json.loads((source / 'status.json').read_text())
assert len(results) == 6
total = 0
for name, result in results.items():
    directory = source / name
    manifest = freeze['installed'].validate(json.loads((directory / 'manifest.json').read_text()))
    cache = ROOT / result['cache']
    assert result['packages'] == len(manifest['packages'])
    for package in manifest['packages']:
        assert sha(cache / package['filename']) == package['sha256']
        freeze['installed'].require_rpm_signature((directory / (package['filename'] + '.signature.txt')).read_text())
        total += 1
    for fixture in manifest['fixtures']:
        assert sha(cache / 'fixtures' / fixture['path']) == fixture['sha256']
    assert sha(cache / 'key.asc') == manifest['signing_key']['sha256']
assert total == 86
test_log = ROOT / 'results/core21-baseline-tests-20261008.log'
text = test_log.read_text()
assert 'Ran 231 tests' in text and text.rstrip().endswith('OK'), text[-1000:]
for path in sorted(source.rglob('*')):
    if path.is_file():
        dest = out / path.relative_to(source)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
for path in [test_log, ROOT / 'results/core21-upgrade-baseline-driver-20261008.log']:
    (out / (path.name + '.gz')).write_bytes(gzip.compress(path.read_bytes(), mtime=0))
for name in ['freeze-core21-baseline-20261008.py', 'record-core21-baseline-20261008.py']:
    shutil.copyfile(ROOT / 'work' / name, out / name)
audit = runpy.run_path(str(ROOT / 'work/write-scoped-audit.py'))
audit['write'](out / 'audit.rst', 'Signed core21 upgrade baseline audit',
    'Scope: a one-shot read-only OBS capture and its metadata; no runtime, recipe or publication change. '
    'All 62 audit-changes items were reviewed. Ten pass and 52 are not applicable. '
    'The six snapshot runs, exact selection negative controls and 231 packaging tests pass.',
    {9: 'New scripts and evidence carry copyright 2026; raw external metadata is preserved verbatim.',
     53: 'No suppression, test bypass or substitute result; snapshot is explicitly separate from lifecycle qualification.',
     54: 'Python context managers close downloads and files; failures prevent a final status manifest; temporary candidates cannot become verified cache entries.',
     55: 'Each worker owns one target/architecture output and RPM database; shared mappings are immutable.',
     56: 'Existing manifest validator checks schema, phases, hashes, safe filenames and native architecture; RPM header identity is checked separately.',
     57: 'Three bounded download workers; streamed downloads and hashes; no container or build duplication.',
     58: 'Changed source, absent/ambiguous/wrong-architecture binary, checksum mismatch and missing verified signature are rejected.',
     59: 'Evidence documents local cache locations, use as an upgrade baseline, signing provenance and pending lifecycle limits.',
     61: 'HTTPS downloads and pinned public key; isolated RPM databases; no credentials, signing secrets or workstation installation.',
     62: '86 signed artifacts and 30 fixture copies reverified; six selection controls and all 231 packaging tests pass.'},
    'No Qore/C++/QPP/module/DataProvider/JNI implementation changed; item is outside this evidence-capture scope.')
record = {
    'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'All six signed core21 baselines preserved and reverified; lifecycle tests remain required.',
    'purpose': 'Keep exact old runtime/SDK artifacts available when newer core builds replace mutable OBS binary URLs.',
    'targets': results, 'rpm_count': total, 'bytes': sum(x['bytes'] for x in results.values()),
    'trust': 'Every RPM has an explicit valid signature verified with the SHA-256-pinned OBS testing public key in a private RPM database. Checksums alone are not accepted.',
    'fixtures': 'All five fixtures per target are downloaded from the immutable core commit and SHA-256 checked.',
    'tests': {'packaging': 231, 'selection': 6, 'signature_and_digest_rechecks': 86},
    'usage': 'Use each archived manifest with its local work/core21-upgrade-baseline-20261008 target cache as the starting package set for upgrade/removal qualification. Preserve these caches until lifecycle testing is complete.',
    'limits': ['This records inputs, not a successful upgrade/removal or dependency-solver run.',
               'ARM package hashes match the existing installed-qualification manifests exactly. x86_64 snapshots are selected from the same core source revision and signature verified; this capture does not claim a new installed x86_64 test.',
               'Distribution packages outside the testing project are not frozen here.',
               'RPM bytes remain in the local cache, not in Git; their current OBS URLs may disappear after a rebuild.',
               'Publication stays disabled; this is not a public package release.'],
    'files_sha256': {str(p.relative_to(ROOT)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}}
(ROOT / 'evidence/core21-upgrade-baseline-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print(f'PASS: {total} signed RPMs and six manifests archived; 231 tests and all 62 audit items reviewed')
