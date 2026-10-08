# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import runpy
import shutil

root = Path.cwd()
report = json.loads((root / 'results/obs-catalog-delivery-20261008/report.json').read_text())
assert len(report['packages']) == 38
assert sum(row['status'] == 'matching pin' for row in report['packages'].values()) == 37
assert report['packages']['module-nats']['status'] == 'not uploaded'
current = json.loads((root / 'catalog.json').read_text())['packages']
for name, row in report['packages'].items():
    assert current[name]['commit'] == row['catalog_commit']
provenance = json.loads((root / 'results/obs-catalog-delivery-20261008/mysql-build-provenance.json').read_text())
assert len(provenance) == 6
activation = json.loads((root / 'results/freetds-native-arm-enablement-20261008/status.json').read_text())
assert activation['result'] == 'applied and read back exactly'
tests = (root / 'results/catalog-freetds-enablement-tests-20261008.log').read_text()
assert 'Ran 224 tests' in tests and tests.rstrip().endswith('OK')
assert 'warning:' not in tests.lower()
qualified = json.loads((root / 'evidence/freetds-rpm-final-20261002.json').read_text())
for target in qualified['targets'].values():
    assert target['build']['exit_code'] == target['installed']['exit_code'] == 0
    for name, digest in target['logs_sha256'].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
out = root / 'evidence/controls/catalog-freetds-20261008'
out.mkdir(exist_ok=True)
for folder in ['obs-catalog-delivery-20261008', 'freetds-native-arm-enablement-20261008']:
    for path in sorted((root / 'results' / folder).iterdir()):
        if not path.is_file():
            continue
        dest = out / folder / path.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == '.log':
            dest.with_suffix('.log.gz').write_bytes(gzip.compress(path.read_bytes(), mtime=0))
        else:
            shutil.copy2(path, dest)
shutil.copy2(root / 'results/obs-current-20261008.xml', out / 'recorded-build-status.xml')
(out / 'packaging-tests.log.gz').write_bytes(gzip.compress(tests.encode(), mtime=0))
shutil.copy2(root / 'work/check-obs-catalog-delivery-20261008.py', out / 'check-catalog.py')
shutil.copy2(Path(__file__), out / 'record.py')
audit = runpy.run_path(str(root / 'work/write-scoped-audit.py'))
passes = {9: 'New metadata, evidence and verifier sources identify 2026; raw OBS responses are preserved verbatim.',
          53: 'The catalog is corrected to the already-qualified MySQL commit. FreeTDS gains only the three native ARM build enables; no source or runtime workaround.',
          54: 'Read-only reconciliation validates command exits and manifest hashes; metadata mutation is guarded by the expected source hash and verified by exact readback.',
          58: 'Pinned RPM Name fields identify packages; inventory-only NATS is explicitly distinguished from committed specs. All dependency graphs resolve before enabling builds.',
          59: 'Evidence states source/build/installed limits separately and retains the corrected initial inventory; publication remains disabled.',
          61: 'Only the authorized testing project metadata changes; no credentials are stored or printed. Existing metadata fields are preserved.',
          62: 'All 224 packaging tests pass. All 38 catalog entries reconciled, 37 match OBS source pins, six MySQL buildinfo hashes verified; all three prior FreeTDS build/install evidence sets remain hash-identical.'}
audit_path = root / 'audits/catalog-freetds-20261008.rst'
audit['write'](audit_path, 'Catalog and FreeTDS ARM enablement audit',
               'Scope: catalog.json, obs/package-freetds-testing.xml and read-only verification evidence. Result: 7 Pass, 55 N/A, 0 Fail across all 62 checklist entries.',
               passes, 'No corresponding runtime, C++, Qore module, test implementation, DataProvider, JNI or public API change.')
record = {'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
          'status': 'Catalog reconciled; FreeTDS native ARM qualification enabled with publication disabled.',
          'catalog': {'entries': 38, 'matching_obs_pins': 37, 'not_uploaded': ['module-nats'],
                      'mysql_old_pin': '46448fbbdc6ed47467d819b0a1fca702aa4d46d7',
                      'mysql_qualified_pin': 'c7ba6b020d76a463d047608eafee5218da0f3c97',
                      'mysql_evidence': 'evidence/xmlsec-and-obs-fixes-20261002.json',
                      'mysql_native_buildinfo': provenance},
          'freetds': {'source_commit': '2b35358523ff5f397e415203e0df37d38825e8eb',
                      'source_revision': 1, 'srcmd5': 'b22b45fb5cb035cf130e2b3e23b40180',
                      'prerequisite_evidence': 'evidence/freetds-rpm-final-20261002.json',
                      'activation': activation},
          'tests': {'packaging': 224, 'failures': 0}, 'audit': str(audit_path.relative_to(root)),
          'limits': ['Native ARM build completion and installed FreeTDS qualification remain pending.',
                     'Live SQL Server/ASE tests and any proprietary OCS variant remain separate gates.',
                     'Source-manifest MD5 identities are verified; prior qualification governs archive SHA-256 and test results.',
                     'The initial inventory assumed spec basename equaled package Name; corrected using the pinned spec. NATS inventory has no committed spec yet and is represented explicitly.',
                     'The recorded build matrix predates ARM enablement; no published repository qualification is claimed.'],
          'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}}
(root / 'evidence/catalog-freetds-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS: catalog/source reconciliation, qualified prior logs, ARM enablement readback and 224 packaging tests recorded')
