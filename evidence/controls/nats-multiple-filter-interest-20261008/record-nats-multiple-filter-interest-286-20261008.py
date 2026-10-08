# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import re
import shutil

root = Path.cwd()
out = root / 'evidence/controls/nats-multiple-filter-interest-20261008'
out.mkdir()
records = []
for variant, count in [('clean', 20), ('control', 10)]:
    for target in ['fedora', 'leap', 'el10']:
        run = root / f'results/{target}-nats-multiple-filter-interest-286-{variant}'
        state = json.loads((run / 'status.json').read_text())
        log = (run / 'tests.log').read_text()
        assert state['exit_code'] == 0 and '-race' in state['command']
        assert len(re.findall(r'^--- PASS:', log, re.M)) == count
        assert not re.search(r'--- FAIL:|--- SKIP:|WARNING: DATA RACE|panic:', log)
        if variant == 'control':
            assert log.count('Missing stream subscription reproduces no responders') == count
        (out / f'{target}-{variant}.log.gz').write_bytes(gzip.compress(log.encode(), mtime=0))
        shutil.copy2(run / 'status.json', out / f'{target}-{variant}-status.json')
        records.append({'target': target, 'variant': variant, 'race_enabled_results': count, 'exit_code': 0})
baseline = []
for line in (root / 'results/fedora-nats-server-candidate-53/build.log').read_text().splitlines():
    if line.startswith('{'):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get('Test') == 'TestJetStreamConsumerMultipleFiltersLastPerSubject':
            baseline.append(row)
assert any(r.get('Action') == 'fail' for r in baseline)
assert any('No response for "1" (error: nats: no responders available for request)' in r.get('Output', '') for r in baseline)
(out / 'candidate53-failed-test.json').write_text(json.dumps(baseline, indent=2) + '\n')
focused = root / 'work/nats-multiple-filter-interest-286-20261008'
for name in ['clean.go', 'control.go']:
    (out / (name + '.gz')).write_bytes(gzip.compress((focused / name).read_bytes(), mtime=0))
shutil.copy2(focused / 'nats-server-multiple-filter-interest-tests.patch', out)
for name in ['prepare-nats-multiple-filter-interest-286-20261008.py',
             'integrate-nats-multiple-filter-interest-286-20261008.py',
             'record-nats-multiple-filter-interest-286-20261008.py',
             'prepare-nats-candidate54-20261008.py', 'run-nats-focused-38.py',
             'nats-multiple-filter-interest-286.json']:
    shutil.copy2(root / 'work' / name, out / name)
verified = json.loads((root / 'results/nats-candidate54-patch-verification-20261008.json').read_text())
assert verified['patches'] == 117 and verified['fuzz'] == 0 and verified['new_patch_offsets'] == 0
assert verified['changed_go_files_from_candidate53'] == ['server/jetstream_consumer_test.go']
assert verified['exact_focused_source_identity']
shutil.copy2(root / 'results/nats-candidate54-patch-verification-20261008.json', out / 'candidate54-verification.json')
for name, count in [('tools', 223), ('runner', 7)]:
    log = (root / f'results/nats-candidate54-{name}-tests-20261008.log').read_text()
    assert re.search(r'Ran ' + str(count) + r' tests in [\d.]+s\n\nOK\s*$', log)
    (out / (name + '-tests.log.gz')).write_bytes(gzip.compress(log.encode(), mtime=0))
loader = importlib.util.spec_from_file_location('audit', root / 'work/write-scoped-audit.py')
audit = importlib.util.module_from_spec(loader)
loader.loader.exec_module(audit)
passes = {
  9: 'The new patch, controls and qualification scripts carry 2026 copyright.',
  53: 'The fixture now establishes its actual route prerequisite through an existing subscription notification. No polling, delay, retry, production change or larger deadline is introduced.',
  54: 'Connections, subscriptions and temporary test interest changes have deferred cleanup; the diagnostic control restores removed interest before running the full original fixture.',
  55: 'The existing Sublist Insert, Remove and notification APIs protect internal state. All 90 runs use the Go race detector without a report.',
  56: 'The correction calls an existing typed helper with the actual cluster and publishing connection. Test results and source verification use explicit structured records.',
  57: 'Only test setup adds a bounded account-route event join. Production runtime has no added operations.',
  58: 'Thirty controls require the exact no-responder error after withdrawing the matched subscription, restore interest, then pass all original message and consumer assertions.',
  59: 'Spec changelog and dependency guide explain the ordering boundary, preserved deadlines and focused/full qualification limits.',
  61: 'The control modifies only disposable server Sublist state inside an isolated test network. No credentials, host services or external endpoints are changed.',
  62: '60 corrected fixture runs and 30 deterministic negative/recovery controls pass across all three distributions under the race detector. All 230 tooling/runner tests pass; 117 patches apply without fuzz and prepared source exactly matches qualification.',
}
audit.write(out / 'audit.rst', 'NATS multiple-filter publication fixture audit',
    'Scope: one test-only readiness correction and focused controls. All 62 checks: 10 Pass, 52 N/A, 0 Fail. Full candidate 53 remains running; candidate 54 RPM/native and repository qualification remain required.',
    passes, 'No Qore module, QPP, DataProvider, JNI, C++ production or Qore-language test changes occur in this Go fixture-only correction.')
record = {'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'Candidate53 first-publication failure corrected; 90 focused race-enabled results and candidate54 source verification pass. Full package qualification remains required.',
    'failure': 'Fedora candidate53 TestJetStreamConsumerMultipleFiltersLastPerSubject: first sendStreamMsg at line 783 returns no responders before consumer creation.',
    'root_cause': 'The API creation reply and stream subscription travel over independently ordered routes. The random publisher can request an acknowledgement before stream interest reaches its ingress.',
    'fix': 'Join the existing event-driven awaitStreamRouteInterest helper before the first of six setup publications.',
    'qualification': records, 'tool_tests': 223, 'runner_tests': 7, 'candidate_patches': 117,
    'limits': ['The diagnostic control models missing ingress interest; it does not reconstruct the historical failed scheduler trace.',
               'The subscription withdrawal, second client and control function are excluded from the package patch.',
               'All original request deadlines, publication counts, delivery values and consumer assertions are preserved.',
               'Candidate53 remains live to collect all failures; candidate54 has not yet been submitted to full builds. Native/installed/repository gates remain open.'],
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}}
(root / 'evidence/nats-multiple-filter-interest-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('Recorded 90 clean race-enabled results, 117-patch integration and the complete 62-check audit.')
