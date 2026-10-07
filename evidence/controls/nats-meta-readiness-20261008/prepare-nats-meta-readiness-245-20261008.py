# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import subprocess

root = Path.cwd()
previous = root / 'work/nats-meta-readiness-244-20261008'
out = root / 'work/nats-meta-readiness-245-20261008'
out.mkdir()
for name in ['jetstream_cluster.go', 'jetstream_api.go']:
    (out / name).write_bytes((previous / name).read_bytes())
test = (previous / 'jetstream_cluster_2_test.go').read_text()
start = test.index('func TestPackagingMetaReadinessAfterRestart(')
end = test.index('// Metadata requests require', start)
prefix, body, suffix = test[:start], test[start:end], test[end:]
needle = '\tresult := make(chan error, 1)\n'
assert body.count(needle) == 1
body = body.replace(needle, '''	ready, cancelReady := context.WithTimeout(context.Background(), 15*time.Second)
	observed := &metadataReadinessContext{Context: ready, awaiting: make(chan struct{})}
	readyResult := make(chan error, 1)
	var readyWorkers sync.WaitGroup
	readyWorkers.Add(1)
	go func() {
		defer readyWorkers.Done()
		readyResult <- awaitMetadataAPILeader(observed, c)
	}()
	defer func() { cancelReady(); readyWorkers.Wait() }()
	select {
	case <-observed.awaiting:
		// Done() is evaluated only after subscriptions are registered and
		// the first application-level metadata readiness check is false.
	case <-ready.Done():
		t.Fatal("readiness helper did not reach its event wait")
	}
''' + needle)
needle = '\tselect {\n\tcase err := <-result:\n'
assert body.count(needle) == 1
body = body.replace(needle, '''	select {
	case err := <-readyResult:
		require_NoError(t, err)
	case <-ready.Done():
		t.Fatal("metadata traffic did not release the readiness barrier")
	}
''' + needle)
body = body.replace('''	ready, cancelReady := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancelReady()
	require_NoError(t, awaitMetadataAPILeader(ready, c))
''', '')
body += '''// Observe a real blocking Context use, without changing the helper under test.
type metadataReadinessContext struct {
	context.Context
	once sync.Once
	awaiting chan struct{}
}

func (ctx *metadataReadinessContext) Done() <-chan struct{} {
	ctx.once.Do(func() { close(ctx.awaiting) })
	return ctx.Context.Done()
}

'''
needle = '\trequire_Error(t, awaitMetadataAPILeader(context.Background(), &cluster{servers: []*Server{s}}))\n'
assert suffix.count(needle) == 1
suffix = suffix.replace(needle, needle + '''	standalone := RunServer(&Options{Port: -1, JetStream: true, StoreDir: t.TempDir()})
	defer standalone.Shutdown()
	require_Error(t, awaitMetadataAPILeader(context.Background(), &cluster{servers: []*Server{standalone}}))
	c := createJetStreamClusterExplicit(t, "META-INPUTS", 3)
	defer c.shutdown()
	ready, stop := context.WithTimeout(context.Background(), 10*time.Second)
	defer stop()
	require_NoError(t, awaitMetadataAPILeader(ready, c))
	// Register on one real metadata peer, then fail on a non-JetStream server.
	// Every temporary subscription must be removed on this partial failure.
	node := c.servers[0].getJetStream().getMetaGroup().(*raft)
	node.Lock()
	transport := node.t.(*defaultTransport)
	transport.c.mu.Lock()
	before := len(transport.c.subs)
	transport.c.mu.Unlock()
	node.Unlock()
	require_Error(t, awaitMetadataAPILeader(context.Background(), &cluster{servers: []*Server{c.servers[0], s}}))
	node.Lock()
	transport.c.mu.Lock()
	after := len(transport.c.subs)
	transport.c.mu.Unlock()
	node.Unlock()
	require_Equal(t, before, after)
''')
test = prefix + body + suffix
(out / 'jetstream_cluster_2_test.go').write_text(test)
subprocess.run(['gofmt', '-w', str(out / 'jetstream_cluster_2_test.go')], check=True)
config = json.loads((root / 'work/nats-meta-readiness-244.json').read_text())
for case in config['cases']:
    case['name'] = case['name'].replace('-244', '-245')
    case['overlays'] = {str(p.relative_to(root)): 'server/' + p.name for p in out.iterdir()}
(root / 'work/nats-meta-readiness-245.json').write_text(json.dumps(config, indent=2) + '\n')
print('Prepared event-resume and partial-subscription-cleanup controls')
