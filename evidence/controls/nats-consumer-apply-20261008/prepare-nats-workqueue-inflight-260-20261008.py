# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import subprocess

root = Path.cwd()
source = root / 'work/nats-prepared-48/nats-server-2.15.0/server'
prior = root / 'work/nats-workqueue-inflight-259-20261008'
out = root / 'work/nats-workqueue-inflight-260-20261008'
out.mkdir()
api = (prior / 'jetstream_api.go').read_text()
api = api.replace('''		defer finish()
		select {
		case <-applied:
			// Re-enter the normal bounded queue, with fresh leadership and
			// assignment checks. No delay, polling, or stale response is used.
			js.apiDispatch(sub, requestClient, acc, subject, reply, rmsg)
		case <-quit:
		case <-s.quitCh:
		}
''', '''		replay := false
		defer func() {
			// Release the retained-request slot before the queue can run it again.
			finish()
			if replay {
				js.apiDispatch(sub, requestClient, acc, subject, reply, rmsg)
			}
		}()
		select {
		case <-applied:
			// Re-enter the normal bounded queue, with fresh leadership and
			// assignment checks. No delay, polling, or stale response is used.
			replay = true
		case <-quit:
		case <-s.quitCh:
		}
''')
(out / 'jetstream_api.go').write_text(api)
cluster = (prior / 'jetstream_cluster.go').read_text()
start = cluster.index('\tfor _, streams := range js.cluster.inflightConsumers {')
end = cluster.index('\tjs.cluster.inflightConsumers = nil\n',start) + len('\tjs.cluster.inflightConsumers = nil\n')
loop = cluster[start:end].replace('js.cluster.', 'cc.')
cluster = cluster[:start] + '\tjs.cluster.clearInflightConsumerProposals()\n' + cluster[end:]
pos = cluster.index('// Return the cluster quit chan.')
cluster = cluster[:pos] + '// Wake retained information requests when their leadership term ends.\n// (Write) Lock held on entry.\nfunc (cc *jetStreamCluster) clearInflightConsumerProposals() {\n' + loop + '}\n\n' + cluster[pos:]
(out / 'jetstream_cluster.go').write_text(cluster)
test = (prior / 'jetstream_cluster_2_test.go').read_text()
test += r'''
// These are lifecycle tests of the pending-request mechanism. Unlike the real
// update/delete reproduction above, the proposals here are deliberately synthetic
// so application, term reset, queue limits and shutdown can be controlled exactly.
func TestJetStreamConsumerInfoPendingDeleteLifecycle(t *testing.T) {
	for _, completion := range []string{"applied", "term_reset", "shutdown", "start_rejected"} {
		t.Run(completion, func(t *testing.T) {
			c := createJetStreamClusterExplicit(t, "INFO-LIFETIME", 3)
			defer c.shutdown()
			meta := c.leader()
			nc, js := jsClientConnect(t, c.randomServer())
			defer nc.Close()
			_, err := js.AddStream(&nats.StreamConfig{Name: "TEST", Subjects: []string{"foo"}, Replicas: 3})
			require_NoError(t, err)
			_, err = js.AddConsumer("TEST", &nats.ConsumerConfig{Durable: "C", AckPolicy: nats.AckExplicitPolicy, Replicas: 3})
			require_NoError(t, err)
			preferred := c.randomNonLeader()
			c.stepDownConsumerLeader(nc, globalAccountName, "TEST", "C", preferred)
			awaitClusterMetaApplied(t, c)
			mjs := meta.getJetStream()
			mjs.mu.RLock()
			cc := mjs.cluster
			ca := mjs.consumerAssignment(globalAccountName, "TEST", "C")
			isConsumerLeader := cc.isConsumerLeader(globalAccountName, "TEST", "C")
			mjs.mu.RUnlock()
			require_NotNil(t, ca)
			require_True(t, !isConsumerLeader)
			subject := fmt.Sprintf(JSApiConsumerInfoT, "TEST", "C")
			body, err := json.Marshal(&ClientInfo{Account: globalAccountName})
			require_NoError(t, err)
			raw := genHeader(nil, ClientInfoHdr, string(body))
			originalRaw := copyBytes(raw)
			client := &client{srv: meta, kind: JETSTREAM}
			client.pa.hdr = len(raw)
			acc := meta.GlobalAccount()
			// Ordinary reads, nonleader reads and absent consumers do not defer.
			deferred, overloaded := mjs.deferConsumerInfoRequest(nil, client, acc, subject, "reply", raw, "TEST", "C")
			require_True(t, !deferred && !overloaded)
			deferred, overloaded = mjs.deferConsumerInfoRequest(nil, client, acc, subject, "reply", raw, "TEST", "missing")
			require_True(t, !deferred && !overloaded)
			oldLimit := atomic.SwapInt64(&mjs.infoQueueLimit, 2)
			defer atomic.StoreInt64(&mjs.infoQueueLimit, oldLimit)
			mjs.mu.Lock()
			cc.trackInflightConsumerProposal(globalAccountName, "TEST", ca, false)
			cc.trackInflightConsumerProposal(globalAccountName, "TEST", ca, true)
			mjs.mu.Unlock()

			// A still-live consumer leader answers while the metadata leader retains
			// its copy. This is the remote-leader variant of the upstream regression.
			if completion == "applied" {
				ci, err := js.ConsumerInfo("TEST", "C")
				require_NoError(t, err)
				require_Equal(t, ci.Name, "C")
				// Clear that synthetic proposal and join its replay through the normal
				// API handler before setting up exact resource-limit assertions below.
				mjs.mu.Lock()
				cc.clearInflightConsumerProposals()
				mjs.mu.Unlock()
				// The direct mechanism checks use the other completion variants; the
				// full shutdown join proves all retained copies have been released.
				meta.Shutdown()
				mjs.mu.RLock()
				pending := cc.pendingConsumerInfos
				mjs.mu.RUnlock()
				require_Equal(t, pending, int64(0))
				return
			}

			type replay struct { subject, reply string; raw []byte; hdr int }
			replayed := make(chan replay, 2)
			api := mjs.apiSubs
			matches := api.Match(subject).psubs
			require_Equal(t, len(matches), 1)
			original := matches[0]
			replacement := &subscription{subject: copyBytes(original.subject),
				icb: func(_ *subscription, c *client, _ *Account, subject, reply string, raw []byte) {
					replayed <- replay{subject, reply, copyBytes(raw), c.pa.hdr}
				}}
			require_NoError(t, api.Remove(original))
			require_NoError(t, api.Insert(replacement))
			defer func() { require_NoError(t, api.Remove(replacement)); require_NoError(t, api.Insert(original)) }()
			if completion == "start_rejected" {
				meta.grMu.Lock()
				meta.grRunning = false
				meta.grMu.Unlock()
				deferred, overloaded = mjs.deferConsumerInfoRequest(nil, client, acc, subject, "rejected", raw, "TEST", "C")
				meta.grMu.Lock()
				meta.grRunning = true
				meta.grMu.Unlock()
				require_True(t, deferred && !overloaded)
				mjs.mu.RLock()
				pending := cc.pendingConsumerInfos
				mjs.mu.RUnlock()
				require_Equal(t, pending, int64(0))
				return
			}
			for i := range 2 {
				deferred, overloaded = mjs.deferConsumerInfoRequest(nil, client, acc, subject, fmt.Sprintf("reply-%d", i), raw, "TEST", "C")
				require_True(t, deferred && !overloaded)
			}
			deferred, overloaded = mjs.deferConsumerInfoRequest(nil, client, acc, subject, "overflow", raw, "TEST", "C")
			require_True(t, !deferred && overloaded)
			for i := range raw { raw[i] = 'x' }
			client.pa.hdr = 0
			mjs.mu.Lock()
			require_Equal(t, cc.pendingConsumerInfos, int64(2))
			inflight := cc.inflightConsumers[globalAccountName]["TEST"]["C"]
			applied := inflight.applied
			cc.removeInflightConsumerProposal(globalAccountName, "TEST", "C")
			mjs.mu.Unlock()
			select {
			case <-applied: t.Fatal("released before all pending operations were applied")
			default:
			}
			if completion == "term_reset" {
				mjs.mu.Lock()
				cc.clearInflightConsumerProposals()
				mjs.mu.Unlock()
				ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
				defer cancel()
				seen := map[string]bool{}
				for range 2 {
					select {
					case r := <-replayed:
						require_Equal(t, r.subject, subject)
						require_Equal(t, r.hdr, len(originalRaw))
						require_True(t, bytes.Equal(r.raw, originalRaw))
						require_True(t, !seen[r.reply])
						seen[r.reply] = true
					case <-ctx.Done(): t.Fatal("retained request was not replayed")
					}
				}
				require_True(t, seen["reply-0"] && seen["reply-1"])
			}
			meta.Shutdown()
			mjs.mu.RLock()
			pending := cc.pendingConsumerInfos
			mjs.mu.RUnlock()
			require_Equal(t, pending, int64(0))
			require_Equal(t, len(replayed), 0)
		})
	}
}
'''
(out / 'jetstream_cluster_2_test.go').write_text(test)
for p in out.glob('*.go'):
 subprocess.run(['gofmt', '-w', str(p)], check=True)
base = json.loads((root / 'work/nats-workqueue-inflight-259.json').read_text())
for c in base['cases']:
 c['name'] = c['name'].replace('259','260')
 c['overlays'] = {str(p.relative_to(root)): 'server/' + p.name for p in out.glob('*.go')}
 c['pattern'] = c['pattern'].replace('ConsumerRecreateDuringMetaApplyLag|', 'ConsumerRecreateDuringMetaApplyLag|ConsumerInfoPendingDeleteLifecycle|')
(root / 'work/nats-workqueue-inflight-260.json').write_text(json.dumps(base,indent=2)+'\n')
print('Prepared completion, term, live-consumer, queue-cap, copied-request and shutdown checks')
