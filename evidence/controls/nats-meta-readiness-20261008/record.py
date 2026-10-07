# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import runpy
import shutil

root = Path.cwd()
out = root / 'evidence/controls/nats-meta-readiness-20261008'
out.mkdir(exist_ok=True)
results = {}
for variant, count in [('245', 3), ('clean-246', 2), ('247', 1)]:
    for target in ['fedora', 'leap', 'el10']:
        name = target + '-nats-meta-readiness-' + variant
        run = root / 'results' / name
        status = json.loads((run / 'status.json').read_text())
        text = (run / 'tests.log').read_text()
        assert status['exit_code'] == 0
        assert len(re.findall(r'^--- PASS:', text, re.M)) == count
        assert not re.search(r'WARNING: DATA RACE|--- FAIL:|\[ERR\]|\[WRN\]', text)
        if variant == '247':
            assert 'restarting the same stream/consumer/metadata leader:' in text
            assert 'first create timed out, ready create succeeded' in text
        results[name] = {'exit_code': 0, 'race_enabled_cases': count}
        shutil.copy2(run / 'status.json', out / (name + '-status.json'))
        (out / (name + '.log.gz')).write_bytes(gzip.compress((run / 'tests.log').read_bytes(), mtime=0))
# Preserve the initial harness's incorrect error-type expectation transparently.
for target in ['fedora', 'leap', 'el10']:
    run = root / 'results' / (target + '-nats-meta-readiness-243')
    text = (run / 'tests.log').read_text()
    assert "Expected one of [nats: timeout], got 'context deadline exceeded'" in text
    shutil.copy2(run / 'status.json', out / (target + '-initial-harness-status.json'))
    (out / (target + '-initial-harness.log.gz')).write_bytes(gzip.compress((run / 'tests.log').read_bytes(), mtime=0))
for number in ['243', '244', '245', '247']:
    script = root / ('work/prepare-nats-meta-readiness-' + number + '-20261008.py')
    shutil.copy2(script, out / script.name)
    directory = root / ('work/nats-meta-readiness-' + number + '-20261008')
    for path in directory.iterdir():
        (out / (number + '-' + path.name + '.gz')).write_bytes(gzip.compress(path.read_bytes(), mtime=0))
    config = root / ('work/nats-meta-readiness-' + number + '.json')
    shutil.copy2(config, out / config.name)
clean = root / 'work/nats-meta-readiness-clean-246-20261008'
patch = clean / 'nats-server-meta-api-ready-tests.patch'
assert '+func awaitMetadataAPILeader' in patch.read_text()
assert not re.search(r'packagingMetaGate|metadataReadinessContext|TestPackagingMetaReadiness', patch.read_text())
for name in ['jetstream_cluster_2_test.go', 'nats-server-meta-api-ready-tests.patch']:
    path = clean / name
    if path.suffix == '.go':
        (out / (name + '.gz')).write_bytes(gzip.compress(path.read_bytes(), mtime=0))
    else:
        shutil.copy2(path, out / name)
shutil.copy2(root / 'work/nats-meta-readiness-clean-246.json', out / 'clean-246-config.json')
shutil.copy2(root / 'work/run-nats-focused-38.py', out / 'run.py')
shutil.copy2(Path(__file__), out / 'record.py')
base = root / 'work/nats-prepared-45/nats-server-2.15.0/server'
original = (base / 'jetstream_cluster_2_test.go').read_text()
qualified = (clean / 'jetstream_cluster_2_test.go').read_text()
expected = '''	ready, cancelReady := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancelReady()
	require_NoError(t, awaitMetadataAPILeader(ready, c))
'''
assert expected in qualified
before, _ = qualified.split('// Metadata requests require', 1)
assert before.replace(expected, '').rstrip() == original.rstrip()
assert (root / 'dependencies/nats-server.spec').read_text().count('nats-server-meta-api-ready-tests.patch') == 0
audit = runpy.run_path(str(root / 'work/write-scoped-audit.py'))
passes = {
    9: 'The test patch and evidence drivers carry 2026 copyright; the upstream test file already ends its copyright range in 2026.',
    53: 'A missing metadata API readiness precondition is joined through actual Raft traffic. No request retries, increased request deadline, production policy change or diagnostic scheduler hook is included in the proposed patch.',
    54: 'All registered subscriptions are removed through defer, including partial registration failure. The event-resume control cancels and joins its readiness worker.',
    55: 'Metadata and transport-client state use their existing mutexes. Notification is coalesced through a buffered channel; all affected runs pass the Go race detector.',
    56: 'The helper uses context.Context, *cluster, *raft and *subscription with checked Raft type conversion; observer records preserve each subscription owner.',
    57: 'Two temporary subscriptions per server, with bounded coalesced notifications. No polling timer, request retry loop or production runtime cost.',
    58: 'Cancelled contexts, empty clusters, disabled JetStream, absent metadata Raft groups, readiness deadline and partial subscription cleanup are checked. Registration errors propagate after deterministic cleanup.',
    59: 'Helper comments and this evidence explain application-level metadata readiness, the controlled schedule, source provenance, retained request deadline and integration limits.',
    61: 'The experiment runs in isolated Docker networks without published ports. The qualified patch changes tests only and introduces no credentials or remote operations.',
    62: '18 final race-enabled cases pass across Fedora, Leap and AlmaLinux: controlled event resume/input cleanup, the clean patch and the exact delete/recreate/ack restart history. The first request deterministically times out after all API handlers reject leadership; the ready request succeeds.'
}
audit['write'](out / 'audit.rst', 'NATS metadata API readiness audit',
    'Scope: focused-qualified test-only readiness correction and its controls. 10 Pass, 52 N/A, 0 Fail. '
    'The patch is not yet registered in the candidate RPM. No C++ implementation or Qore module changes.',
    passes, 'No Qore module, QPP, DataProvider, C++ implementation, Qore-language test or JAR change in this scope.')
record = {
    'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'The missing metadata API readiness precondition is reproduced and its test-only correction passes focused qualification. RPM integration and a full candidate rebuild remain required.',
    'root_cause': 'The restart fixture waits for R1 stream/consumer leadership and reads their state, but those conditions can precede publication of the new application-level metadata leader. Every stream-create handler then takes its normal non-leader return. Electing/publishing a leader later cannot recover the already discarded request, which ends with context deadline exceeded.',
    'controlled_schedule': 'Use the original create/delete/recreate history, 22 restored messages and five acknowledged deliveries. Public placement tags select the same server for the stream, consumer and metadata leader before restart. Pause the real processLeaderChange callback before API leadership publication; verify all three real API handlers decline TEST2. Release the callback immediately after those events. The original ten-second request still expires; the next ready request succeeds.',
    'fix': 'Before AddStream(TEST2), await an application-level metadata leader under the JetStream state lock. Observe real Raft appends/replies for progress, remove all temporary subscriptions on every exit, and retain the original client request deadline.',
    'validation': {'final_race_enabled_cases': 18, 'results': results,
                   'clean_patch_files': ['server/jetstream_cluster_2_test.go'],
                   'patch_applies_without_fuzz_or_offsets': True,
                   'no_production_Go_source_changes': True},
    'source_sha256': {name: hashlib.sha256((base / name).read_bytes()).hexdigest()
                      for name in ['jetstream_cluster.go', 'jetstream_api.go', 'jetstream_cluster_2_test.go']},
    'limits': ['The historical failed RPM did not contain request tracing. This proves a real reachable fixture defect with the same failed operation and timeout; it does not claim a captured trace of that historical execution.',
               'Diagnostic scheduler gates and Context observation are excluded from the proposed RPM patch. The clean patch is separately compiled and tested on all three distributions.',
               'The first diagnostic run expected nats.ErrTimeout, but this JetStream API returns context.DeadlineExceeded. That harness assertion was corrected and the failure logs are retained.',
               'The registration-error cleanup test uses a valid first metadata peer followed by a server without JetStream; an internal transport Subscribe failure is handled but not independently fault-injected.',
               'Historical sparse-consumer performance, atomic-batch, workqueue and fail-tracking gates remain separate. Full builds, skip review, client/module, native OBS and repository lifecycle qualification are still required.'],
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
}
(root / 'evidence/nats-meta-readiness-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('Recorded and audited the focused-qualified NATS metadata readiness correction')
