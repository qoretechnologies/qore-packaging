# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib
import json
import subprocess

root = Path.cwd()
source = root / 'work/nats-prepared-53/nats-server-2.15.0'
out = root / 'work/nats-multiple-filter-interest-286-20261008'
out.mkdir()
original = (source / 'server/jetstream_consumer_test.go').read_text()
name = 'TestJetStreamConsumerMultipleFiltersLastPerSubject'
a = original.index('func ' + name + '(')
b = original.index('\nfunc ', a + 1)
body = original[a:b]
needle = '\tsendStreamMsg(t, nc, "one", "1")\n'
assert body.count(needle) == 1
addition = '''	// The creation reply and stream subscriptions travel on separate routes.
	awaitStreamRouteInterest(t, c, nc, "TEST")
'''
clean = original[:a] + body.replace(needle, addition + needle) + original[b:]
(out / 'clean.go').write_text(clean)
subprocess.run(['gofmt', '-w', str(out / 'clean.go')], check=True)
patch = '# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n# Join stream route interest before the multiple-filter fixture publishes its setup messages.\n'
patch += ''.join(difflib.unified_diff(original.splitlines(True), (out / 'clean.go').read_text().splitlines(True),
                                    fromfile='a/server/jetstream_consumer_test.go', tofile='b/server/jetstream_consumer_test.go'))
(out / 'nats-server-multiple-filter-interest-tests.patch').write_text(patch)
control = '''	// Model the independent account-route propagation boundary without sleep.
	leader := c.streamLeader(globalAccountName, "TEST")
	require_NotNil(t, leader)
	var ingress *Server
	for _, srv := range c.servers {
		if srv != leader {
			ingress = srv
			break
		}
	}
	require_NotNil(t, ingress)
	remote, remoteJS := jsClientConnect(t, ingress)
	defer remote.Close()
	awaitStreamRouteInterest(t, c, remote, "TEST")
	list := ingress.GlobalAccount().sl
	matched := list.Match("one")
	require_Equal(t, len(matched.qsubs), 0)
	subscriptions := append([]*subscription(nil), matched.psubs...)
	require_True(t, len(subscriptions) > 0)
	restore := func() {
		for _, subscription := range subscriptions {
			require_NoError(t, list.Insert(subscription))
		}
		subscriptions = nil
	}
	defer restore()
	for _, subscription := range subscriptions {
		require_NoError(t, list.Remove(subscription))
	}
	require_Equal(t, len(list.Match("one").psubs), 0)
	_, err := remote.Request("one", []byte("1"), 500*time.Millisecond)
	require_Error(t, err, nats.ErrNoResponders)
	restore()
	awaitExactSubjectInterest(t, list, "one")
	nc, js = remote, remoteJS
	t.Log("Missing stream subscription reproduces no responders; full multiple-filter regression follows after restoration")
'''
control_body = body.replace(name, 'TestPackagingMultipleFilterPublicationInterest', 1)
control_body = control_body.replace(needle, control + addition + needle)
# The appended control declares err before the original consumer creation.
control_body = control_body.replace('\t_, err := js.AddConsumer(', '\t_, err = js.AddConsumer(')
(out / 'control.go').write_text(original + '\n' + control_body)
subprocess.run(['gofmt', '-w', str(out / 'control.go')], check=True)
cases = []
for variant, count, pattern in [('clean', 20, '^' + name + '$'),
                                ('control', 10, '^TestPackagingMultipleFilterPublicationInterest$')]:
    for target in ['fedora', 'leap', 'el10']:
        cases.append({'name': f'{target}-nats-multiple-filter-interest-286-{variant}', 'target': target,
                      'count': count, 'race': True, 'pattern': pattern,
                      'sublist': str((source / 'server/sublist.go').relative_to(root)),
                      'overlays': {str((out / (variant + '.go')).relative_to(root)): 'server/jetstream_consumer_test.go'}})
(root / 'work/nats-multiple-filter-interest-286.json').write_text(json.dumps({
    'source': str(source.relative_to(root)), 'workers': 3, 'cases': cases}, indent=2) + '\n')
print('Prepared clean fixture correction and deterministic missing-interest controls on three distributions.')
