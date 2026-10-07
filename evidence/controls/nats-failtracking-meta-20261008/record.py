# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import runpy
import shutil

root = Path.cwd()
out = root / 'evidence/controls/nats-failtracking-meta-20261008'
out.mkdir(exist_ok=True)
results = {}
for variant, count in [('meta-250', 1), ('meta-253', 3), ('clean-252', 10)]:
    for target in ['fedora', 'leap', 'el10']:
        name = target + '-nats-failtracking-' + variant
        run = root / 'results' / name
        status = json.loads((run / 'status.json').read_text())
        text = (run / 'tests.log').read_text()
        assert status['exit_code'] == 0, name
        assert '-race' in status['command']
        passed = len(re.findall(r'^\s*--- PASS:', text, re.M))
        assert passed == count, (name, passed)
        assert not re.search(r'WARNING: DATA RACE|--- FAIL:|\[ERR\]|\[WRN\]', text)
        if variant == 'meta-253':
            for state in ['false', 'true']:
                assert f'wait={state}: preserved 25 ordered messages' in text
        results[name] = {'exit_code': 0, 'race_enabled_reported_cases': count}
        shutil.copy2(run / 'status.json', out / (name + '-status.json'))
        (out / (name + '.log.gz')).write_bytes(gzip.compress((run / 'tests.log').read_bytes(), mtime=0))
for variant in ['248', '249', '251']:
    for target in ['fedora', 'leap', 'el10']:
        name = target + '-nats-failtracking-meta-' + variant
        run = root / 'results' / name
        status = json.loads((run / 'status.json').read_text())
        assert status['exit_code'] != 0
        shutil.copy2(run / 'status.json', out / (name + '-status.json'))
        (out / (name + '.log.gz')).write_bytes(gzip.compress((run / 'tests.log').read_bytes(), mtime=0))
for number in ['248', '249', '250', '251', '253']:
    script = root / f'work/prepare-nats-failtracking-meta-{number}-20261008.py'
    shutil.copy2(script, out / script.name)
    directory = root / f'work/nats-failtracking-meta-{number}-20261008'
    for path in directory.iterdir():
        (out / (number + '-' + path.name + '.gz')).write_bytes(gzip.compress(path.read_bytes(), mtime=0))
    shutil.copy2(root / f'work/nats-failtracking-meta-{number}.json', out / f'config-{number}.json')
clean = root / 'work/nats-failtracking-clean-252-20261008'
patch = clean / 'nats-server-failtracking-meta-ready-tests.patch'
assert not re.search(r'packagingMetaGate|PackagingFailTracking|packagingMetadataWaitContext', patch.read_text())
shutil.copy2(patch, out / patch.name)
(out / 'clean-jetstream_cluster_3_test.go.gz').write_bytes(gzip.compress((clean / 'jetstream_cluster_3_test.go').read_bytes(), mtime=0))
shutil.copy2(root / 'work/nats-failtracking-clean-252.json', out / 'config-clean-252.json')
shutil.copy2(root / 'work/run-nats-focused-38.py', out / 'run.py')
shutil.copy2(Path(__file__), out / 'record.py')
source = root / 'work/nats-prepared-46/nats-server-2.15.0/server/jetstream_cluster_3_test.go'
historical = root / 'results/fedora-nats-server-candidate-39/rpmbuild/BUILD/nats-server-2.15.0-build/nats-server-2.15.0/server/jetstream_cluster_3_test.go'
def test_body(path):
    text = path.read_text()
    start = text.index('func TestJetStreamClusterStreamFailTracking(')
    return text[start:text.index('\nfunc ', start + 1)]
assert test_body(historical) == test_body(source)
original = source.read_text()
qualified = (clean / source.name).read_text()
addition = '''
	// Stream leadership and publication can recover before the metadata API.
	ready, cancelReady := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancelReady()
	require_NoError(t, awaitMetadataAPILeader(ready, c))
'''
assert qualified.count(addition) == 1
assert qualified.replace(addition, '', 1) == original
audit = runpy.run_path(str(root / 'work/write-scoped-audit.py'))
passes = {
    9: 'New patch, qualification scripts and evidence carry 2026 copyright; the upstream Go test already ends its copyright range in 2026.',
    53: 'The clean change joins a missing metadata API precondition after an intentional restart. It retains the existing request deadline and assertions, with no retries or production changes.',
    54: 'The clean helper context is cancelled with defer. Controlled request workers are cancelled and joined; temporary stream observers and scheduling gates are released on failure paths.',
    55: 'The previously qualified readiness helper protects metadata state with existing locks. Diagnostic gate publication uses atomic.Pointer, progress uses channels, and every final run enables the Go race detector.',
    56: 'Typed context, cluster, Server, subscription and response values are used. The source correction reuses the already qualified readiness helper.',
    57: 'The source change adds only temporary test observers around one readiness boundary. It introduces no production cost or polling timer; request deadlines are unchanged.',
    58: 'Paired controls require the original request to time out only after all three real handlers decline it; the corrected control requires no request while API publication is paused, followed by successful first-request completion. Normal follower returns after publication are allowed.',
    59: 'Patch comments and this record document the readiness distinction, historical source identity, exact scheduling controls and limits. Repository integration and full RPM builds remain explicit gates.',
    61: 'Tests run in isolated Docker networks without published ports; no credentials, external messages or production configuration changes are introduced.',
    62: 'Paired original/fixed scheduling controls pass on all three distributions and preserve 25 ordered, deduplicated messages after the R3-to-R1 update. The clean original test passes 10 race-enabled runs per target. Historical candidate39 and candidate46 test bodies are byte-identical.'
}
audit['write'](out / 'audit.rst', 'NATS replica-update metadata readiness audit',
    'Scope: focused-qualified test-only correction and controls. 10 Pass, 52 N/A, 0 Fail. '
    'The patch has not yet been integrated into the RPM candidate. No C++ implementation changes.',
    passes, 'No corresponding Qore module, QPP, DataProvider, C++ implementation, Qore-language test or JAR change.')
record = {
    'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'A missing metadata API readiness precondition in the replica-update fixture is reproduced and corrected; focused qualification passed on all three distributions. RPM integration remains required.',
    'root_cause': 'The randomly restarted non-stream leader may be the metadata leader. Stream reset/recovery, leader changes and deduplicated publication can complete while the new metadata Raft leader has not published application-level API leadership. Every stream-update handler then declines the request; publishing leadership later does not recover it.',
    'fix': 'Join the already qualified awaitMetadataAPILeader helper immediately before reducing stream replicas. Keep the original client request deadline and all original state/order assertions.',
    'historical_source': {'file_sha256': hashlib.sha256(historical.read_bytes()).hexdigest(),
        'test_body_sha256': hashlib.sha256(test_body(historical).encode()).hexdigest(),
        'candidate39_and_candidate46_test_bodies_identical': True},
    'controlled_schedule': ['Create the original R3 stream and publish duplicate message-ID batches.',
        'Use public preferred-placement stepdown to put stream leadership away from the metadata leader; restart that eligible non-stream leader after resetting its stream Raft state.',
        'Pause the real metadata leadership callback before API publication, join stream recovery and select the restarted stream leader through actual Raft events.',
        'The original update reaches and is declined by all three API handlers; release metadata publication immediately afterward and verify the original ten-second deadline still expires.',
        'The paired corrected control enters the actual readiness helper event wait before metadata publication is released; no request is sent while publication is paused and the first update succeeds afterward. The other two followers may take their ordinary nonleader returns.',
        'Both paths finish with one stream replica and all 25 ordered, deduplicated messages.'],
    'qualification': {'final_reported_race_cases': sum(v['race_enabled_reported_cases'] for v in results.values()),
        'results': results, 'clean_original_test_runs': 30, 'paired_schedule_subtests': 6},
    'initial_harness_corrections': ['Control248 used a nonexistent require_Nil helper; it was replaced with an explicit pointer check.',
        'Control249 assumed a stepdown response meant its tagged target had already become leader. Control250 uses public Preferred placement, joins the restarted stream current state, then observes actual Raft traffic until target leadership is published. Earlier failed logs are retained.',
        'Control251 incorrectly rejected normal follower returns after metadata leadership was published. Control253 checks for premature requests only while publication is still paused, then requires the first request to succeed.'],
    'limits': ['The historical failing build did not record request tracing. The deterministic control proves a reachable fixture defect with the same lifecycle and failed operation, not a recovered trace of that historical execution.',
        'The scheduling gates, placement selection, observer witness and request traces are diagnostic-only and absent from the clean RPM patch.',
        'The initial stream-reset delay is preserved from the original fixture in the control; no new timing sleep or polling loop is introduced.',
        'The patch depends on candidate46 Patch108. Full RPM integration, skip review, client/module, native OBS and repository lifecycle gates remain.',
        'Historical sparse-consumer performance, atomic-batch and workqueue failures remain separate unresolved gates.'],
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
}
(root / 'evidence/nats-failtracking-meta-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('Recorded and audited the paired replica-update readiness controls and clean fixture correction')
