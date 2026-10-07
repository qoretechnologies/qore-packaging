# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import subprocess

root = Path.cwd()
source = root / 'work/nats-prepared-45/nats-server-2.15.0/server'
out = root / 'work/nats-meta-readiness-243-20261008'
out.mkdir()
cluster = (source / 'jetstream_cluster.go').read_text()
marker = 'func (js *jetStream) processLeaderChange(isLeader bool, term uint64) {'
assert cluster.count(marker) == 1
cluster = cluster.replace(marker, '''// Diagnostic-only scheduler gate; never part of the package recipe.
type packagingMetaReadinessGate struct {
	arrived chan *Server
	resume chan struct{}
	published chan *Server
	requests chan *Server
}

var packagingMetaGate atomic.Pointer[packagingMetaReadinessGate]

''' + marker)
begin = cluster.index(marker)
end = cluster.index('\nfunc ', begin + 1)
body = cluster[begin:end]
needle = '\tif isLeader {\n\t\ts.Noticef("Self is new JetStream cluster metadata leader")'
assert body.count(needle) == 1
body = body.replace(needle, '''	gate := packagingMetaGate.Load()
	if gate != nil && isLeader {
		gate.arrived <- s
		select {
		case <-gate.resume:
		case <-s.quitCh:
			return
		}
	}
''' + needle)
needle = '\tjs.cluster.term = term\n'
assert body.count(needle) == 1
body = body.replace(needle, needle + '''	if gate != nil && isLeader {
		gate.published <- s
	}
''')
cluster = cluster[:begin] + body + cluster[end:]
api = (source / 'jetstream_api.go').read_text()
begin = api.index('func (s *Server) jsStreamCreateRequest(')
end = api.index('\nfunc ', begin + 1)
body = api[begin:end]
needle = '\t\tif !s.JetStreamIsLeader() {\n\t\t\treturn\n\t\t}'
assert body.count(needle) == 1
body = body.replace(needle, '''		if !s.JetStreamIsLeader() {
			if gate := packagingMetaGate.Load(); gate != nil && subject == "$JS.API.STREAM.CREATE.TEST2" {
				gate.requests <- s
			}
			return
		}''')
api = api[:begin] + body + api[end:]
test = (source / 'jetstream_cluster_2_test.go').read_text()
test += r'''

// Diagnostic-only: preserve real metadata election and restart, but hold the
// scheduler before publishing the new metadata leader to the API handlers.
func TestPackagingMetaReadinessAfterRestart(t *testing.T) {
	c := createJetStreamClusterExplicit(t, "META-RESTART", 3)
	defer c.shutdown()
	nc, js := jsClientConnect(t, c.randomServer())
	defer nc.Close()
	_, err := js.AddStream(&nats.StreamConfig{Name: "TEST"})
	require_NoError(t, err)
	_, err = js.Publish("TEST", []byte("OK"))
	require_NoError(t, err)
	_, err = js.AddConsumer("TEST", &nats.ConsumerConfig{Durable: "dlc", AckPolicy: nats.AckExplicitPolicy})
	require_NoError(t, err)
	awaitClusterMetaApplied(t, c)
	gate := &packagingMetaReadinessGate{arrived: make(chan *Server, 8), resume: make(chan struct{}),
		published: make(chan *Server, 8), requests: make(chan *Server, 8)}
	var release sync.Once
	defer func() { release.Do(func() { close(gate.resume) }); packagingMetaGate.Store(nil) }()
	packagingMetaGate.Store(gate)
	oldLeader := c.leader()
	require_NotNil(t, oldLeader)
	oldLeader.Shutdown()
	c.restartServer(oldLeader)
	select {
	case leader := <-gate.arrived:
		t.Logf("new metadata leader elected, API publication paused: %s", leader.Name())
	case <-time.After(15 * time.Second):
		t.Fatal("metadata election did not reach scheduler gate")
	}
	// These are the same entity-readiness conditions used by the failing test.
	c.waitOnStreamLeader(globalAccountName, "TEST")
	c.waitOnConsumerLeader(globalAccountName, "TEST", "dlc")
	nc, js = jsClientConnect(t, c.randomServer())
	defer nc.Close()
	info, err := js.StreamInfo("TEST")
	require_NoError(t, err)
	require_Equal(t, info.State.Msgs, uint64(1))
	_, err = js.ConsumerInfo("TEST", "dlc")
	require_NoError(t, err)
	for _, server := range c.servers {
		require_False(t, server.JetStreamIsLeader())
		require_False(t, server.getJetStream().isLeaderless())
	}
	result := make(chan error, 1)
	go func() {
		_, err := js.AddStream(&nats.StreamConfig{Name: "TEST2"})
		result <- err
	}()
	seen := make(map[*Server]bool)
	for len(seen) < len(c.servers) {
		select {
		case server := <-gate.requests:
			seen[server] = true
		case <-time.After(10 * time.Second):
			t.Fatal("stream-create request did not reach every API handler")
		}
	}
	// Resume immediately after each real handler takes its normal non-leader
	// return. A later healthy leader cannot recover the already dropped request.
	release.Do(func() { close(gate.resume) })
	select {
	case leader := <-gate.published:
		require_True(t, leader.JetStreamIsLeader())
	case <-time.After(10 * time.Second):
		t.Fatal("metadata leadership was not published")
	}
	select {
	case err := <-result:
		require_Error(t, err, nats.ErrTimeout)
	case <-time.After(15 * time.Second):
		t.Fatal("original ten-second stream-create request did not terminate")
	}
	// The original operation succeeds after actual metadata readiness.
	_, err = js.AddStream(&nats.StreamConfig{Name: "TEST2"})
	require_NoError(t, err)
	require_NoError(t, js.DeleteStream("TEST2"))
	t.Log("entity reads succeeded before metadata readiness; first create timed out, ready create succeeded")
}
'''
for name, text in [('jetstream_cluster.go', cluster), ('jetstream_api.go', api),
                   ('jetstream_cluster_2_test.go', test)]:
    path = out / name
    path.write_text(text)
    subprocess.run(['gofmt', '-w', str(path)], check=True)
cases = []
for target in ['fedora', 'leap', 'el10']:
    cases.append({'name': target + '-nats-meta-readiness-243', 'target': target, 'count': 1,
                  'race': True, 'pattern': '^TestPackagingMetaReadinessAfterRestart$',
                  'sublist': str((source / 'sublist.go').relative_to(root)),
                  'overlays': {str(p.relative_to(root)): 'server/' + p.name for p in out.iterdir()}})
(root / 'work/nats-meta-readiness-243.json').write_text(json.dumps({
    'source': str(source.parent.relative_to(root)), 'workers': 3, 'cases': cases}, indent=2) + '\n')
print('Prepared real-restart metadata-readiness experiment; no proposed production fix')
