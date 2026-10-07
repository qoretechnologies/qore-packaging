# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import subprocess

root = Path.cwd()
source = root / 'work/nats-prepared-46/nats-server-2.15.0/server'
out = root / 'work/nats-failtracking-meta-249-20261008'
out.mkdir()
cluster = (root / 'work/nats-meta-readiness-247-20261008/jetstream_cluster.go').read_text()
original_cluster = (source / 'jetstream_cluster.go').read_text()
assert original_cluster == (root / 'work/nats-prepared-45/nats-server-2.15.0/server/jetstream_cluster.go').read_text()
(out / 'jetstream_cluster.go').write_text(cluster)
api = (source / 'jetstream_api.go').read_text()
a = api.index('func (s *Server) jsStreamUpdateRequest(')
b = api.index('\nfunc ', a + 1)
body = api[a:b]
needle = '\t\tif !s.JetStreamIsLeader() {\n\t\t\treturn\n\t\t}'
assert body.count(needle) == 1
body = body.replace(needle, '''		if !s.JetStreamIsLeader() {
			if gate := packagingMetaGate.Load(); gate != nil && subject == "$JS.API.STREAM.UPDATE.TEST" {
				gate.requests <- s
			}
			return
		}''')
(out / 'jetstream_api.go').write_text(api[:a] + body + api[b:])
test = (source / 'jetstream_cluster_3_test.go').read_text()
test += r'''

// Diagnostic-only scheduling control for the original fail-tracking lifecycle.
// Placement selects a member allowed by the original random choices.
func TestPackagingFailTrackingMetadataReadiness(t *testing.T) {
	c := createJetStreamClusterWithTemplateAndModHook(t, jsClusterTempl, "R3S", 3,
		func(sn, cn, storeDir, conf string) string {
			return conf + fmt.Sprintf("\nserver_tags: [%q]\n", sn)
		})
	defer c.shutdown()
	nc, js := jsClientConnect(t, c.randomServer())
	defer nc.Close()
	_, err := js.AddStream(&nats.StreamConfig{Name: "TEST", Subjects: []string{"foo"}, Replicas: 3})
	require_NoError(t, err)
	m := nats.NewMsg("foo")
	m.Data = []byte("OK")
	b, bsz := 0, 5
	sendBatch := func() {
		for i := b * bsz; i < b*bsz+bsz; i++ {
			m.Header.Set(JSMsgId, fmt.Sprintf("ID:%d", i))
			_, err := js.PublishMsg(m)
			require_NoError(t, err)
			_, err = js.PublishMsg(m)
			require_NoError(t, err)
		}
		b++
	}
	sendBatch()
	chosenMeta := c.leader()
	require_NotNil(t, chosenMeta)
	currentStream := c.streamLeader(globalAccountName, "TEST")
	var other *Server
	for _, server := range c.servers {
		if server != chosenMeta && server != currentStream {
			other = server
			break
		}
	}
	require_NotNil(t, other)
	stepdown := func(target *Server) {
		payload, err := json.Marshal(&JSApiLeaderStepdownRequest{Placement: &Placement{Tags: []string{target.Name()}}})
		require_NoError(t, err)
		msg, err := nc.Request(fmt.Sprintf(JSApiStreamLeaderStepDownT, "TEST"), payload, time.Second)
		require_NoError(t, err)
		var response JSApiStreamLeaderStepDownResponse
		require_NoError(t, json.Unmarshal(msg.Data, &response))
		require_True(t, response.Error == nil)
		c.waitOnStreamLeader(globalAccountName, "TEST")
		require_True(t, c.streamLeader(globalAccountName, "TEST") == target)
	}
	stepdown(other)
	sendBatch()
	// The original fixture chooses a random non-stream leader here. Select
	// the metadata leader, which is one of those valid choices.
	nl := chosenMeta
	require_True(t, nl != c.streamLeader(globalAccountName, "TEST"))
	require_True(t, nl == c.leader())
	mset, err := nl.GlobalAccount().lookupStream("TEST")
	require_NoError(t, err)
	mset.resetClusteredState(mset.raftNode(), nil)
	time.Sleep(100 * time.Millisecond) // Unchanged original reset interval.
	awaitClusterMetaApplied(t, c)
	gate := &packagingMetaReadinessGate{arrived: make(chan *Server, 8), resume: make(chan struct{}),
		published: make(chan *Server, 8), requests: make(chan *Server, 8)}
	var release sync.Once
	defer func() { release.Do(func() { close(gate.resume) }); packagingMetaGate.Store(nil) }()
	packagingMetaGate.Store(gate)
	nl.Shutdown()
	nl.WaitForShutdown()
	sendBatch()
	nl = c.restartServer(nl)
	sendBatch()
	select {
	case leader := <-gate.arrived:
		t.Logf("metadata elected but API publication paused: %s", leader.Name())
	case <-time.After(15 * time.Second):
		t.Fatal("metadata election did not reach scheduler gate")
	}
	stepdown(nl)
	sendBatch()
	for _, server := range c.servers {
		require_False(t, server.JetStreamIsLeader())
		require_False(t, server.getJetStream().isLeaderless())
	}
	result := make(chan error, 1)
	requestContext, cancelRequest := context.WithTimeout(context.Background(), 10*time.Second)
	var workers sync.WaitGroup
	workers.Add(1)
	defer func() { cancelRequest(); workers.Wait() }()
	go func() {
		defer workers.Done()
		_, err := js.UpdateStream(&nats.StreamConfig{Name: "TEST", Subjects: []string{"foo"}, Replicas: 1}, nats.Context(requestContext))
		result <- err
	}()
	seen := make(map[*Server]bool)
	for len(seen) < len(c.servers) {
		select {
		case server := <-gate.requests:
			seen[server] = true
		case <-requestContext.Done():
			t.Fatal("update request did not reach every API handler")
		}
	}
	release.Do(func() { close(gate.resume) })
	select {
	case <-gate.published:
	case <-time.After(10 * time.Second):
		t.Fatal("metadata leadership was not published")
	}
	require_Error(t, <-result, context.DeadlineExceeded)
	ready, cancelReady := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancelReady()
	require_NoError(t, awaitMetadataAPILeader(ready, c))
	_, err = js.UpdateStream(&nats.StreamConfig{Name: "TEST", Subjects: []string{"foo"}, Replicas: 1})
	require_NoError(t, err)
	// Verify the original ordered, deduplicated history after the replica change.
	sub, err := js.SubscribeSync("foo")
	require_NoError(t, err)
	defer sub.Unsubscribe()
	for i := 0; i < b*bsz; i++ {
		message, err := sub.NextMsg(time.Second)
		require_NoError(t, err)
		require_Equal(t, message.Header.Get(JSMsgId), fmt.Sprintf("ID:%d", i))
		require_NoError(t, message.AckSync())
	}
	info, err := js.StreamInfo("TEST")
	require_NoError(t, err)
	require_Equal(t, info.State.Msgs, uint64(b*bsz))
	require_Equal(t, info.Config.Replicas, 1)
	t.Logf("original update timed out before metadata readiness; ready update preserved %d ordered messages", b*bsz)
}
'''
if '\n\t"context"\n' not in test:
    test = test.replace('import (\n', 'import (\n\t"context"\n', 1)
(out / 'jetstream_cluster_3_test.go').write_text(test)
for path in out.iterdir():
    subprocess.run(['gofmt', '-w', str(path)], check=True)
cases = []
for target in ['fedora', 'leap', 'el10']:
    cases.append({'name': target + '-nats-failtracking-meta-249', 'target': target, 'count': 1,
                  'race': True, 'pattern': '^TestPackagingFailTrackingMetadataReadiness$',
                  'sublist': str((source / 'sublist.go').relative_to(root)),
                  'overlays': {str(p.relative_to(root)): 'server/' + p.name for p in out.iterdir()}})
(root / 'work/nats-failtracking-meta-249.json').write_text(json.dumps({
    'source': str(source.parent.relative_to(root)), 'workers': 3, 'cases': cases}, indent=2) + '\n')
print('Prepared replica-update metadata-readiness experiment with original restart/data history')
