# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib
import json
import subprocess

root = Path.cwd()
source = root / 'work/nats-prepared-47/nats-server-2.15.0/server'
out = root / 'work/nats-extended-interest-254-20261008'
out.mkdir()
original = (source / 'jetstream_cluster_1_test.go').read_text()
a = original.index('func TestJetStreamClusterExtendedStreamInfo(')
b = original.index('\nfunc ', a + 1)
body = original[a:b]
needle = '\tfetchMsgs(t, sub, 10, 5*time.Second)\n'
assert body.count(needle) == 1
addition = '''	// Consumer creation replies and pull-request route interest arrive independently.
	ingress := c.serverByName(nc.ConnectedServerName())
	require_NotNil(t, ingress)
	awaitExactSubjectInterest(t, ingress.GlobalAccount().sl, fmt.Sprintf(JSApiRequestNextT, "TEST", "dlc"))
'''
body = body.replace(needle, addition + needle)
clean = original[:a] + body + original[b:]
(out / 'clean.go').write_text(clean)
subprocess.run(['gofmt', '-w', str(out / 'clean.go')], check=True)
clean = (out / 'clean.go').read_text()
patch = '# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n'
patch += '# Join the extended-info fixture consumer pull-handler interest before its first fetch.\n'
patch += ''.join(difflib.unified_diff(original.splitlines(True), clean.splitlines(True),
    fromfile='a/server/jetstream_cluster_1_test.go', tofile='b/server/jetstream_cluster_1_test.go'))
(out / 'nats-server-extended-info-interest-tests.patch').write_text(patch)

# Reuse the qualified missing-interest control at this exact fixture's first fetch.
old = (root / 'work/nats-unknown-delivery-control-203/jetstream_cluster_1_test.go').read_text()
x = old.index('\t// Reproduce the exact startup ordering without sleep:')
y = old.index('\t// We only fetch 1 message here', x)
control = old[x:y]
control = control.replace('leader := c.consumerLeader', 'pullLeader := c.consumerLeader')
control = control.replace('require_NotNil(t, leader)', 'require_NotNil(t, pullLeader)')
control = control.replace('server != leader', 'server != pullLeader')
control = control.replace('"CONSUMER"', '"dlc"').replace('NEXT.TEST.CONSUMER', 'NEXT.TEST.dlc')
control = control.replace('complete unknown-delivery regression', 'complete extended-info regression')
diagnostic = body.replace('TestJetStreamClusterExtendedStreamInfo', 'TestPackagingExtendedStreamPullInterest', 1)
diagnostic = diagnostic.replace(needle, control + needle)
(out / 'control.go').write_text(original + '\n' + diagnostic)
subprocess.run(['gofmt', '-w', str(out / 'control.go')], check=True)
cases = []
for variant, count, pattern in [('clean', 20, '^TestJetStreamClusterExtendedStreamInfo$'),
                                ('control', 10, '^TestPackagingExtendedStreamPullInterest$')]:
    for target in ['fedora', 'leap', 'el10']:
        cases.append({'name': f'{target}-nats-extended-interest-254-{variant}', 'target': target,
                      'count': count, 'race': True, 'pattern': pattern,
                      'sublist': str((source / 'sublist.go').relative_to(root)),
                      'overlays': {str((out / (variant + '.go')).relative_to(root)): 'server/jetstream_cluster_1_test.go'}})
(root / 'work/nats-extended-interest-254.json').write_text(json.dumps({
    'source': str(source.parent.relative_to(root)), 'workers': 3, 'cases': cases}, indent=2) + '\n')
print('Prepared clean extended-info readiness correction and exact first-fetch negative controls')
