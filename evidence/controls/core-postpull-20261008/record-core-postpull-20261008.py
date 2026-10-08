# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Verify and archive the reviewed Qore fixes against the pulled develop head."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import runpy
import shutil
import subprocess

root = Path(__file__).resolve().parent.parent
repo = root.parent / 'qore'
out = root / 'evidence/controls/core-postpull-20261008'
out.mkdir()
base = root / 'results/core-postpull-20261008'
csv = root / 'results/core-csv-final3-20261008'
assert json.loads((base / 'status.json').read_text())['exit_code'] == 0
csv_status = json.loads((csv / 'status.json').read_text())
assert csv_status['exit_code'] == 0
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip()
assert head == '9f94a962fefd7de5d4e2720e6d541ae334a2a959'
before = json.loads((base / 'source.json').read_text())['files_sha256']
for p, digest in before.items():
    if '/audits/' not in p and p != 'examples/test/qore/misc/hash-lookup-native.rst':
        assert hashlib.sha256((repo / p).read_bytes()).hexdigest() == digest, p
for p, digest in csv_status['source_sha256'].items():
    assert hashlib.sha256((repo / p).read_bytes()).hexdigest() == digest, p


def suite(path):
    log = path.read_text()
    rows = re.findall(r'Ran (\d+) test cases?, (\d+) succeeded \((\d+) assertions\)', log)
    assert len(rows) == 1 and rows[0][0] == rows[0][1], path
    assert not re.search(r'(?im)(warning encountered|^warning:|^error:|CMake Error)', log), path
    return {'cases_reported': int(rows[0][0]), 'assertions': int(rows[0][2]),
            'skipped': len(re.findall(r'^Skipped:', log, re.M))}


results = {}
for mode in ('debug', 'release'):
    steps = json.loads((base / mode / 'steps.json').read_text())
    assert len(steps) == 20 and all(s['exit_code'] == 0 for s in steps)
    assert (base / mode / 'native.log').read_text() == 'PASS: 348 hash lookup checks\n'
    memory = sorted((base / mode).glob('*valgrind.log'))
    assert len(memory) == 5
    for path in memory:
        text = path.read_text()
        assert 'ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)' in text
        assert all(re.search(kind + r' lost:\s+0 bytes in 0 blocks', text)
                   for kind in ('definitely', 'indirectly', 'possibly'))
        warnings = [line for line in text.splitlines() if 'Warning:' in line]
        assert len(warnings) == 1 and 'zero subprog, missing DW_AT_abstract_origin' in warnings[0]
    tests = {p.stem: suite(p) for p in (base / mode).glob('*.log')
             if p.stem not in ('configure', 'build', 'updated-qlib-build', 'native') and 'valgrind' not in p.stem}
    for path in (csv / mode).glob('*.log'):
        if path.stem != 'build':
            tests[path.stem] = suite(path)
    assert len(tests) == 15 and all(not t['skipped'] for t in tests.values())
    assert sum(t['cases_reported'] for t in tests.values()) == 118
    assert sum(t['assertions'] for t in tests.values()) == 5780
    integration = suite(root / f'results/core-loader-integration-postpull-20261008/{mode}.log')
    assert integration == {'cases_reported': 39, 'assertions': 356, 'skipped': 5}
    results[mode] = {'native_checks': 348, 'tests': tests, 'functional_cases': 118,
                     'functional_assertions': 5780, 'valgrind_runs': 5, 'memory_errors': 0,
                     'definite_indirect_possible_lost_bytes': 0,
                     'salesforce_offline_cases': 34, 'salesforce_assertions': 356, 'salesforce_live_skips': 5}
assert all(step['exit_code'] == 0 for step in json.loads((csv / 'steps.json').read_text()))
docs = json.loads((root / 'results/core-hash-docs-postpull-20261008/status.json').read_text())
assert len(docs) == 4 and all(step['exit_code'] == 0 for step in docs)

write = runpy.run_path(str(root / 'work/write-scoped-audit.py'))['write']
passes = {
    7: 'CsvProfiler.qc remains a separated class file without parse directives.',
    8: 'No include directive is added.',
    9: 'The module, edited test and new audit carry Copyright 2026.',
    13: 'CsvProfiler.qtest retains %modern.',
    14: 'The edited qtest remains executable (0755).',
    15: 'The local qlib path precedes hard relative imports. Separated DataProvider/CsvUtil modules use their directory paths; flat QUnit/FsUtil use .qm paths.',
    16: 'All four required modules are delivered with Qore; no external module dependency is introduced.',
    20: 'The change and added cases operate on in-memory bytes. Existing file-action integration uses its temporary fixture and on_exit cleanup.',
    53: 'The conversion result is retained and its target-encoding invariant is asserted. The required cross-encoding conversion still validates UTF-8; no warning filter or behavior bypass is added.',
    54: 'Local strings own conversion data. Existing exception handling selects the documented Latin-1 fallback; each malformed sample is followed by a successful valid sample.',
    55: 'No mutable shared state or process configuration is introduced.',
    56: 'The result is a typed string; tests use typed binary, TabularTextFormat and TabularWorkbookGrid values.',
    57: 'The same single validation conversion runs; the debug postcondition is a constant-size encoding comparison.',
    58: 'Empty input, 11 valid boundary sequences and 15 malformed sequences cover truncation, overlong encodings, surrogates, out-of-range characters, byte preservation and recovery.',
    59: 'The comment explains why conversion to another encoding is necessary. Existing public encoding/fallback documentation remains accurate; no public behavior change requires a release-note claim.',
    61: 'No new I/O, shell construction, credentials or unchecked byte access. CSV integration verifies the original payload bytes are preserved.',
    62: 'Both module targets rebuild. Six CSV suites pass in each mode: 53 cases and 3436 assertions, including 11 profiler cases/211 assertions, without functional or Qore compiler warnings. C++ is unchanged in this CSV scope; Valgrind is covered separately for the core fixes.'}
csv_audit = repo / 'examples/test/qlib/CsvUtil/audits/CsvProfiler.rst'
write(csv_audit, 'CSV encoding validation audit',
      'Scope: CsvProfiler.qc and CsvProfiler.qtest after pulling 9f94a962f. '
      f'All 62 checks reviewed: {len(passes)} Pass, {62-len(passes)} N/A, 0 implementation failures. '
      'The ignored-return warning is fixed; raw qualification is in qore-packaging/results/core-csv-final3-20261008. '
      'The build retains only the separately requested optional ngtcp2 configure diagnostics; their approval remains pending. '
      'The first local fixture attempts used the wrong forms of relative imports; directory modules must be required by directory, not by their entry-point .qm file. The corrected fixture passes in both modes.',
      passes, 'No corresponding new module, QPP class, C++ implementation, DataProvider registration, JNI integration or cancellation operation in this CSV scope.')

loader = repo / 'examples/test/qore/misc/module-loader/audits/separated-module-path.rst'
text = loader.read_text()
text = text.replace('prior integration and negative evidence remains in evidence/core-separated-path-fix-20261008.json.',
                    'post-pull Salesforce integration at module-grpc cdf5fd994e2baf46007bb643b59626e1a5434ea3 passes 34 offline cases/356 assertions in each mode; five credential-dependent live cases are skipped. Historical negative evidence remains in evidence/core-separated-path-fix-20261008.json.')
loader.write_text(text)

directories = ['core-postpull-20261008', 'core-csv-postpull-20261008', 'core-csv-final-20261008',
               'core-csv-final2-20261008', 'core-csv-final3-20261008', 'core-hash-docs-postpull-20261008',
               'core-loader-integration-postpull-20261008']
for name in directories:
    source = root / 'results' / name
    for p in sorted(source.rglob('*')):
        if not p.is_file() or p.suffix not in ('.log', '.json', '.cpp'):
            continue
        destination = out / name / p.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix == '.log':
            destination.with_suffix('.log.gz').write_bytes(gzip.compress(p.read_bytes(), mtime=0))
        else:
            shutil.copyfile(p, destination)
for name in ['qualify-core-postpull-20261008.py', 'finish-core-csv-postpull-20261008.py',
             'qualify-core-csv-final-20261008.py', 'qualify-core-csv-final2-20261008.py',
             'qualify-core-csv-final3-20261008.py', 'audit-core-postpull-20261008.py',
             'check-core-hash-docs-postpull-20261008.py', 'record-core-postpull-20261008.py']:
    shutil.copyfile(root / 'work' / name, out / name)
paths = subprocess.check_output(['git', 'diff', '--name-only'], cwd=repo, text=True).splitlines()
paths += subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=repo, text=True).splitlines()
for path in [p for p in paths if '/audits/' in p]:
    destination = out / 'audits' / Path(path).name
    destination.parent.mkdir(exist_ok=True)
    shutil.copyfile(repo / path, destination)
record = {'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
          'status': 'All post-pull tests and reviews complete; commit/push awaits only two previously requested external diagnostic decisions.',
          'base_commit': head,
          'fixes': ['Clear hash exists output on conversion/member-validation failure; retain the remote QoreHashKeyHelper.',
                    'Normalize directory modules found through cwd-relative search paths before constructing module metadata.',
                    'Consume and assert the UTF-16 validation result in CsvProfiler without changing its UTF-8/Latin-1 decision.'],
          'qualification': results,
          'audit': {'hash': {'pass': 19, 'na': 43, 'fail': 0}, 'loader': {'pass': 16, 'na': 46, 'fail': 0},
                    'csv': {'pass': len(passes), 'na': 62-len(passes), 'fail': 0}},
          'pending_decisions': ['evidence/ngtcp2-backend-diagnostics-20261008.json',
                                'evidence/core-separated-pcre-diagnostic-20261008.json'],
          'approved_diagnostic': 'The existing exact GCC/Valgrind missing-DW_AT_abstract_origin diagnostic remains visible; no suppressions.',
          'limits': ['Loader memory runs use the documented PCRE2 interpreter mode; ordinary tests use JIT, whose exact external diagnostic remains pending.',
                     'Salesforce live tests require credentials and are skipped; offline module loading and protocol integration are covered.',
                     'Updated RPM/OBS builds and full repository qualification remain separate gates.',
                     'Initial CSV fixture failures and strict configure-warning checker stop are preserved; no production bypass was added.'],
          'source_sha256': {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in paths},
          'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(out.rglob('*')) if p.is_file()}}
(root / 'evidence/core-postpull-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
subprocess.run(['git', 'diff', '--check'], cwd=repo, check=True)
print('PASS: both modes, 348 native checks + 118 cases/5780 assertions each; ten clean Valgrind runs; all 186 audit entries reviewed')
