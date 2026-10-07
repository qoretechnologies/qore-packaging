# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import runpy
import shutil
import subprocess

root = Path.cwd()
out = root / 'evidence/controls/nats-extended-interest-20261008'
out.mkdir(exist_ok=True)
source = root / 'work/nats-extended-interest-254-20261008'
results = []
for variant, count in [('clean', 20), ('control', 10)]:
    for target in ['fedora', 'leap', 'el10']:
        name = target + '-nats-extended-interest-254-' + variant
        run = root / 'results' / name
        status = json.loads((run / 'status.json').read_text())
        text = (run / 'tests.log').read_text()
        assert status['exit_code'] == 0 and '-race' in status['command'], name
        assert len(re.findall(r'^--- PASS:', text, re.M)) == count, name
        assert not re.search(r'WARNING: DATA RACE|--- FAIL:|\[ERR\]|\[WRN\]', text)
        if variant == 'control':
            assert text.count('Missing pull subscription reproduced no responders; complete extended-info regression follows after restoration') == count
        results.append({'target': target, 'variant': variant, 'race_enabled_cases': count, 'exit_code': 0})
        shutil.copy2(run / 'status.json', out / (name + '-status.json'))
        (out / (name + '.log.gz')).write_bytes(gzip.compress((run / 'tests.log').read_bytes(), mtime=0))
failed_source = root / 'results/fedora-nats-server-candidate-46/rpmbuild/BUILD/nats-server-2.15.0-build/nats-server-2.15.0/server/jetstream_cluster_1_test.go'
original = failed_source.read_text()
assert original == (root / 'work/nats-prepared-47/nats-server-2.15.0/server/jetstream_cluster_1_test.go').read_text()
assert original.splitlines()[2023].strip() == 'fetchMsgs(t, sub, 10, 5*time.Second)'
addition = '''	// Consumer creation replies and pull-request route interest arrive independently.
	ingress := c.serverByName(nc.ConnectedServerName())
	require_NotNil(t, ingress)
	awaitExactSubjectInterest(t, ingress.GlobalAccount().sl, fmt.Sprintf(JSApiRequestNextT, "TEST", "dlc"))
'''
clean = (source / 'clean.go').read_text()
assert clean.count(addition) == 1 and clean.replace(addition, '', 1) == original
failed = []
with (root / 'results/fedora-nats-server-candidate-46/build.log').open() as log:
    for line in log:
        if not line.startswith('{'):
            continue
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get('Test') == 'TestJetStreamClusterExtendedStreamInfo':
            failed.append(entry)
assert any(entry.get('Action') == 'fail' for entry in failed)
(out / 'candidate46-failed-test.json').write_text(json.dumps(failed, indent=2) + '\n')
for name in ['clean.go', 'control.go']:
    (out / (name + '.gz')).write_bytes(gzip.compress((source / name).read_bytes(), mtime=0))
patch = source / 'nats-server-extended-info-interest-tests.patch'
shutil.copy2(patch, out / patch.name)
check = subprocess.run(['patch', '--dry-run', '--fuzz=0', '-p1', '-d', str(root / 'work/nats-prepared-47/nats-server-2.15.0'),
                        '-i', str(patch)], capture_output=True, text=True, check=True)
assert 'offset' not in check.stdout.lower() and not check.stderr
(out / 'patch-check.txt').write_text(check.stdout)
for name in ['work/prepare-nats-extended-interest-254-20261008.py', 'work/nats-extended-interest-254.json',
             'work/run-nats-focused-38.py']:
    shutil.copy2(root / name, out / Path(name).name)
shutil.copy2(Path(__file__), out / 'record.py')
audit = runpy.run_path(str(root / 'work/write-scoped-audit.py'))
passes = {
    9: 'The patch, qualification scripts and evidence carry 2026 copyright; the upstream test file already ends its copyright range in 2026.',
    53: 'The fixture joins its exact consumer pull-handler subscription before Fetch. No retry, sleep, timeout change, runtime change or diagnostic suppression is introduced.',
    54: 'The existing notification helper clears its observer and stops its timer with defer. The diagnostic control restores every removed subscription through deferred cleanup, including early failure.',
    55: 'Subscription removal/insertion and notification use the existing synchronized Sublist API. All 90 clean/control runs pass the Go race detector.',
    56: 'Typed server, subscription and response values are used; JSApiRequestNextT constructs the exact TEST/dlc consumer subject.',
    57: 'One temporary test observer joins an existing subscription event. There is no production cost or polling loop.',
    58: 'The negative control requires the exact nats.ErrNoResponders result before restoration and then completes the unchanged extended-info assertions. The ingress is checked before accessing its account.',
    59: 'The source comment and evidence distinguish independent API and account routes and record the failed RPM source line, control adaptation and qualification limits.',
    61: 'Tests run on isolated Docker networks without published ports or credentials. Production access and configuration are unchanged.',
    62: '60 complete original-fixture runs and 30 missing-interest controls pass across three distributions. The clean diff consists only of the four readiness lines; controls preserve the original restart, message count and stream/consumer replica checks.'
}
audit['write'](out / 'audit.rst', 'NATS extended stream-info readiness audit',
    'Scope: focused-qualified fixture synchronization and controls. 10 Pass, 52 N/A, 0 Fail. '
    'RPM integration and the full combined build remain required. No C++ implementation changes.',
    passes, 'No corresponding Qore module, QPP, DataProvider, C++ implementation, Qore-language test or JAR change.')
record = {
    'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'The candidate46 first-fetch failure is corrected and focused qualification passed; combined RPM integration remains required.',
    'failure': 'Fedora candidate46 TestJetStreamClusterExtendedStreamInfo returns nats.ErrNoResponders at jetstream_cluster_1_test.go:2024, its first fetchMsgs call after successful PullSubscribe.',
    'root_cause': 'Consumer creation replies travel over the API route independently from consumer pull-handler interest on the account route. The fixture can send its first fetch before that interest reaches its randomly chosen ingress.',
    'fix': 'Join the exact TEST/dlc pull-request subject through the existing Sublist notification helper before the first fetch. All original request deadlines, message assertions and replica checks remain unchanged.',
    'qualification': {'race_enabled_cases': 90, 'results': results,
        'clean_patch_only_adds_readiness_precondition': True, 'patch_fuzz_and_offsets': 0},
    'source_sha256': hashlib.sha256(failed_source.read_bytes()).hexdigest(),
    'prior_mechanism_evidence': ['evidence/nats-candidate37-focused-20261007.json', 'evidence/nats-mirror-pull-interest-20261007.json'],
    'limits': ['The diagnostic control temporarily removes existing interest on a nonleader ingress, reproduces the exact no-responder result, and restores it before completing this fixture. It models the propagation boundary; it is not a trace of the historical failed scheduling.',
        'Subscription manipulation, the second bound client and the control function are excluded from the package patch.',
        'Candidate46 full builds were still running when the failure was isolated. Other failures, historical gates, native OBS and repository lifecycle checks remain independent requirements.'],
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
}
(root / 'evidence/nats-extended-interest-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('Recorded 90 passing race-enabled extended-info runs and exact first-fetch negative controls')
