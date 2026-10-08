# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import re
import shutil

root = Path.cwd()
out = root / 'evidence/controls/nats-peer-commit-20261008'
out.mkdir()
records = []
for target in ['fedora', 'leap', 'el10']:
    run = root / f'results/{target}-nats-peer-commit-287'
    state = json.loads((run/'status.json').read_text())
    log = (run/'tests.log').read_text()
    assert state['exit_code'] == 0 and '-race' in state['command']
    assert len(re.findall(r'^--- PASS:', log, re.M)) == 100
    assert len(re.findall(r'^    --- PASS:', log, re.M)) == 200
    assert log.count('Speculative peer count is 2 with 3 durable peers') == 20
    assert not re.search(r'--- FAIL:|--- SKIP:|WARNING:|panic:', log)
    (out/f'{target}.log.gz').write_bytes(gzip.compress(log.encode(), mtime=0))
    shutil.copy2(run/'status.json', out/f'{target}-status.json')
    records.append({'target': target, 'top_level_results':100, 'subtest_results':200,
                    'race_enabled':True, 'exit_code':0})
baseline = []
for line in (root/'results/fedora-nats-server-candidate-53/build.log').read_text().splitlines():
    if line.startswith('{'):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get('Test') == 'TestNRGLeaderResurrectsRemovedPeers':
            baseline.append(row)
assert any(row.get('Action') == 'fail' for row in baseline)
assert any('3 != 2' in row.get('Output', '') for row in baseline)
(out/'candidate53-failed-test.json').write_text(json.dumps(baseline, indent=2)+'\n')
focused = root/'work/nats-peer-commit-287-20261008'
(out/'raft_test.go.gz').write_bytes(gzip.compress((focused/'clean.go').read_bytes(), mtime=0))
shutil.copy2(focused/'nats-server-peer-commit-tests.patch', out)
for name in ['prepare-nats-peer-commit-287-20261008.py', 'record-nats-peer-commit-287-20261008.py',
             'prepare-nats-candidate55-20261008.py', 'run-nats-focused-38.py', 'nats-peer-commit-287.json']:
    shutil.copy2(root/'work'/name, out/name)
verified = json.loads((root/'results/nats-candidate55-patch-verification-20261008.json').read_text())
assert verified['patches'] == 118 and verified['fuzz'] == 0 and verified['new_patch_offsets'] == 0
assert verified['changed_go_files_from_candidate54'] == ['server/raft_test.go']
assert verified['exact_focused_source_identity']
shutil.copy2(root/'results/nats-candidate55-patch-verification-20261008.json', out/'candidate55-verification.json')
shutil.copy2(root/'work/nats-server-candidate-55/nats-server.spec', out/'nats-server.spec')
for name, count in [('tools',223), ('runner',7)]:
    log = (root/f'results/nats-candidate55-{name}-tests-20261008.log').read_text()
    assert re.search(r'Ran '+str(count)+r' tests in [\d.]+s\n\nOK\s*$',log)
    (out/(name+'-tests.log.gz')).write_bytes(gzip.compress(log.encode(),mtime=0))
loader=importlib.util.spec_from_file_location('audit', root/'work/write-scoped-audit.py')
audit=importlib.util.module_from_spec(loader)
loader.loader.exec_module(audit)
passes={
    9:'The fixture patch and qualification scripts carry 2026 copyright; the modified upstream test already has 2026 copyright.',
    53:'The restart test now observes committed removal, its actual precondition. The original two-second deadline and restart assertions remain. No production change, polling, delay, retry or suppression is introduced.',
    54:'The progress observer is removed by defer on success, closed-node and deadline paths. An existing observer is preserved on rejection. The actual fixture timer and cluster have deferred cleanup.',
    55:'Progress installation, state inspection and cleanup use the Raft mutex. The existing application callback signals under that mutex, so completion before registration is visible and later completion cannot be missed. All 300 top-level results and 600 nested subtest results run under the race detector.',
    56:'The helper takes a typed Raft node, peer ID and receive-only deadline channel. The state tests use typed booleans and the durable-state control uses decoded peerState.',
    57:'The change is confined to tests and uses an event notification with a bounded original deadline. No extra runtime cost is added to the production binary.',
    58:'Controls reject unknown, speculative, still-present and pending membership; accept committed membership even if observed after completion; reject closed nodes and preserve an occupied observer. Deadline delivery is deterministic through a closed test channel.',
    59:'Spec changelog and dependency guide explain the speculative/durable distinction, unchanged budget and remaining full-package gates. Source comments identify the event-ordering invariant.',
    61:'Controls operate on disposable nodes and their temporary peer-state files inside isolated test networks. No credential or external-service change occurs.',
    62:'60 corrected restart runs, 60 durable-boundary controls, 60 observer suites, 60 existing truncation suites and 60 progress tests pass. The boundary control drives the actual commit path and verifies persisted three-to-two membership. All 230 tooling tests pass and all 118 candidate patches apply without fuzz.',
}
audit.write(out/'audit.rst', 'NATS committed peer-removal fixture audit',
    'Scope: one Go restart fixture, its event-driven observer and focused regression controls. All 62 checks: 10 Pass, 52 N/A, 0 Fail. Full candidate55 RPM/native and repository qualification remain required.',
    passes, 'No Qore module, QPP, DataProvider, JNI, C++ production or Qore-language test changes occur in this Go fixture correction.')
record={
    'schema':1, 'date':'2026-10-08', 'copyright':'Copyright 2026 Qore Technologies, s.r.o.',
    'status':'Fedora candidate53 peer restart failure root-caused and corrected; all 300 focused race-enabled top-level results pass. Candidate55 prepared; full RPM/native qualification remains required.',
    'failure':'TestNRGLeaderResurrectsRemovedPeers restarted with three peers after the test observed a speculative two-peer map.',
    'root_cause':'sendMembershipChange removes the peer speculatively before applyCommit/removePeer writes durable membership. The fixture stops its in-memory WAL before commit when it waits only for Peers() length.',
    'fix':'Observe a removed-peer commit marker, peer absence and completion of membership change through the existing application-progress notification, retaining the original two-second deadline.',
    'qualification':records, 'tool_tests':223, 'runner_tests':7, 'candidate_patches':118,
    'limits':[
        'The manual node reproduces the exact speculative/durable state boundary; it does not reconstruct the historical scheduler trace.',
        'The manual control drives applyCommit directly. The corrected original three-node restart test separately exercises real proposal, quorum, application and restart behavior.',
        'Candidate53 remains live to collect any further full-suite failures. Candidate55 has not yet run the complete RPM matrix.',
        'Native architecture, installed client/module and repository delivery gates remain open.'],
    'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}}
(root/'evidence/nats-peer-commit-20261008.json').write_text(json.dumps(record,indent=2)+'\n')
print('Recorded 300 race-enabled top-level results, 600 nested results and candidate55 source identity.')
