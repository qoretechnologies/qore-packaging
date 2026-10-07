# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import subprocess

root = Path.cwd()
previous = root / 'work/nats-meta-readiness-243-20261008'
out = root / 'work/nats-meta-readiness-244-20261008'
out.mkdir()
for name in ['jetstream_cluster.go', 'jetstream_api.go']:
    (out / name).write_bytes((previous / name).read_bytes())
test = (previous / 'jetstream_cluster_2_test.go').read_text()
assert test.count('require_Error(t, err, nats.ErrTimeout)') >= 1
start = test.index('func TestPackagingMetaReadinessAfterRestart(')
prefix, body = test[:start], test[start:]
body = body.replace('require_Error(t, err, nats.ErrTimeout)', 'require_Error(t, err, context.DeadlineExceeded)')
needle = '\tresult := make(chan error, 1)\n'
assert body.count(needle) == 1
body = body.replace(needle, '''	probe, cancelProbe := context.WithTimeout(context.Background(), 50*time.Millisecond)
	err = awaitMetadataAPILeader(probe, c)
	cancelProbe()
	require_Error(t, err, context.DeadlineExceeded)
''' + needle)
needle = '\t// The original operation succeeds after actual metadata readiness.\n'
assert body.count(needle) == 1
body = body.replace(needle, needle + '''	ready, cancelReady := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancelReady()
	require_NoError(t, awaitMetadataAPILeader(ready, c))
''')
helper = r'''

// Metadata requests require the application-level leader, not merely a
// recovered stream/consumer or an elected Raft leader. Observe real metadata
// traffic until the leader publication is complete; do not poll or retry APIs.
func awaitMetadataAPILeader(ctx context.Context, c *cluster) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if len(c.servers) == 0 {
		return errors.New("cluster has no servers")
	}
	type observer struct {
		node *raft
		sub *subscription
	}
	var observers []observer
	defer func() {
		for _, observed := range observers {
			observed.node.Lock()
			observed.node.unsubscribe(observed.sub)
			observed.node.Unlock()
		}
	}()
	progress := make(chan struct{}, 1)
	notify := func(_ *subscription, _ *client, _ *Account, _, _ string, _ []byte) {
		select {
		case progress <- struct{}{}:
		default:
		}
	}
	for _, server := range c.servers {
		js := server.getJetStream()
		if js == nil {
			return errors.New("JetStream is unavailable")
		}
		node, ok := js.getMetaGroup().(*raft)
		if !ok {
			return errors.New("metadata Raft group is unavailable")
		}
		node.Lock()
		for _, subject := range []string{node.asubj, node.areply} {
			sub, err := node.subscribe(subject, notify)
			if err != nil {
				node.Unlock()
				return err
			}
			observers = append(observers, observer{node, sub})
		}
		node.Unlock()
	}
	for {
		if err := ctx.Err(); err != nil {
			return err
		}
		for _, server := range c.servers {
			js := server.getJetStream()
			js.mu.RLock()
			ready := server.JetStreamIsLeader()
			js.mu.RUnlock()
			if ready {
				return nil
			}
		}
		select {
		case <-progress:
			// The observer may precede metadata application. A later real
			// heartbeat supplies another event without a polling timer.
		case <-ctx.Done():
			return ctx.Err()
		}
	}
}

func TestMetadataAPILeaderReadinessInputs(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	require_Error(t, awaitMetadataAPILeader(ctx, &cluster{}), context.Canceled)
	require_Error(t, awaitMetadataAPILeader(context.Background(), &cluster{}))
	s := RunServer(&Options{Port: -1})
	defer s.Shutdown()
	require_Error(t, awaitMetadataAPILeader(context.Background(), &cluster{servers: []*Server{s}}))
}
'''
test = prefix + body + helper
start = test.index('func TestJetStreamClusterDeleteAndRestoreAndRestart(')
end = test.index('\nfunc ', start + 1)
body = test[start:end]
needle = '\t_, err = js.AddStream(&nats.StreamConfig{Name: "TEST2"})\n'
assert body.count(needle) == 1
body = body.replace(needle, '''	ready, cancelReady := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancelReady()
	require_NoError(t, awaitMetadataAPILeader(ready, c))
''' + needle)
test = test[:start] + body + test[end:]
(out / 'jetstream_cluster_2_test.go').write_text(test)
subprocess.run(['gofmt', '-w', str(out / 'jetstream_cluster_2_test.go')], check=True)
config = json.loads((root / 'work/nats-meta-readiness-243.json').read_text())
for case in config['cases']:
    case['name'] = case['name'].replace('-243', '-244')
    case['pattern'] = '^Test(PackagingMetaReadinessAfterRestart|MetadataAPILeaderReadinessInputs|JetStreamClusterDeleteAndRestoreAndRestart)$'
    case['overlays'] = {str(p.relative_to(root)): 'server/' + p.name for p in out.iterdir()}
(root / 'work/nats-meta-readiness-244.json').write_text(json.dumps(config, indent=2) + '\n')
print('Prepared corrected timeout control and metadata API readiness barrier')
