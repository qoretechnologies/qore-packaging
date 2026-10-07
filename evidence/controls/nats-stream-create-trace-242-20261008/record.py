# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import shutil

root = Path.cwd()
out = root / 'evidence/controls/nats-stream-create-trace-242-20261008'
out.mkdir(exist_ok=True)
rows = {}
for target in ['fedora', 'leap', 'el10']:
    run = root / 'results' / (target + '-nats-stream-create-trace-242')
    status = json.loads((run / 'status.json').read_text())
    assert status['exit_code'] == 0
    text = (run / 'tests.log').read_text()
    assert text.count('--- PASS: TestJetStreamClusterDeleteAndRestoreAndRestart') == 30
    assert text.count('CREATE-TRACE response') == 30
    assert text.count('CREATE-TRACE completed err=<nil>') == 30
    assert not re.search(r'--- FAIL:|WARNING: DATA RACE|recovering=true|leader=false', text)
    responses = re.findall(r'CREATE-TRACE response server="[^"]+" reply="([^"]+)" body=(.*)', text)
    assert len({reply for reply, _ in responses}) == 30
    for reply, body in responses:
        response = json.loads(body)
        assert 'error' not in response
        assert response['config']['name'] == 'TEST2'
        assert 'reply="' + reply + '" member=true responded=false recovering=false' in text
    rows[target] = {'exit_code': 0, 'race_enabled_passes': 30,
                    'successful_stream_create_responses': 30,
                    'result_directory': str(run.relative_to(root))}
    shutil.copy2(run / 'status.json', out / (target + '-status.json'))
    (out / (target + '-tests.log.gz')).write_bytes(gzip.compress((run / 'tests.log').read_bytes(), mtime=0))
for source, name in [(Path(__file__), 'record.py'),
                     (root / 'work/prepare-nats-stream-create-trace-242-20261007.py', 'prepare.py'),
                     (root / 'work/run-nats-focused-38.py', 'run.py'),
                     (root / 'work/nats-stream-create-trace-242.json', 'config.json')]:
    shutil.copy2(source, out / name)
overlays = root / 'work/nats-stream-create-trace-242-20261007'
source = root / 'work/nats-prepared-45/nats-server-2.15.0/server'
source_hashes = {}
for file in sorted(overlays.iterdir()):
    source_hashes[file.name] = hashlib.sha256((source / file.name).read_bytes()).hexdigest()
    (out / (file.name + '.gz')).write_bytes(gzip.compress(file.read_bytes(), mtime=0))
record = {
    'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'The correctly instrumented stream-create test passes 90 race-enabled runs; the historical timeout remains unresolved.',
    'correction': 'Retained candidate44 source identifies the failed call as AddStream(TEST2), after ConsumerInfo has succeeded. Earlier ConsumerInfo-only traces did not observe the failed operation.',
    'previous_evidence': 'evidence/nats-candidate45-full-results-20261007.json',
    'instrumentation': ['Actual TEST2 API request and return branches',
                        'Metadata stream assignment, membership and recovery state',
                        'Stream leadership and response ownership',
                        'Actual API response and client result'],
    'results': rows, 'candidate45_original_source_sha256': source_hashes,
    'limits': ['These diagnostic-only overlays are not registered in the RPM and make no functional change.',
               'Every observed assignment that hosted TEST2 was non-recovering and had not responded; each operation emitted exactly one successful response.',
               'No failed request was captured. These passes cannot establish which stage caused the historical timeout, nor justify a reply-ownership or timeout workaround.',
               'Metadata election/readiness and response routing remain hypotheses requiring an observed failure or a controlled lifecycle proof.'],
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
}
(root / 'evidence/nats-stream-create-trace-242-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('Recorded 90 stream-create passes without closing the unresolved timeout gate')
