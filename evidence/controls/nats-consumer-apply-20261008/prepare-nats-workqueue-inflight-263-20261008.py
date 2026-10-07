# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import subprocess
root=Path.cwd()
prior=root/'work/nats-workqueue-inflight-262-20261008'
out=root/'work/nats-workqueue-inflight-263-20261008'
out.mkdir()
for name in ['jetstream_api.go','jetstream_cluster.go','jetstream_cluster_2_test.go']:
 s=(prior/name).read_text()
 if name=='jetstream_cluster_2_test.go':
  needle='''			if completion == "live_consumer" {
				ci, err := js.ConsumerInfo("TEST", "C")'''
  assert s.count(needle)==1
  s=s.replace(needle, '''			if completion == "live_consumer" {
				finished := make(chan struct{})
				var notified sync.Once
				api := mjs.apiSubs
				matches := api.Match(subject).psubs
				require_Equal(t, len(matches), 1)
				original := matches[0]
				replacement := &subscription{subject: copyBytes(original.subject),
					icb: func(sub *subscription, c *client, acc *Account, subject, reply string, raw []byte) {
						original.icb(sub, c, acc, subject, reply, raw)
						notified.Do(func() { close(finished) })
					}}
				require_NoError(t, api.Remove(original))
				require_NoError(t, api.Insert(replacement))
				defer func() { require_NoError(t, api.Remove(replacement)); require_NoError(t, api.Insert(original)) }()
				ci, err := js.ConsumerInfo("TEST", "C")''')
  needle='''				require_Equal(t, ci.Name, "C")
				// Clear that synthetic proposal and join its replay through the normal
				// API handler before setting up exact resource-limit assertions below.'''
  assert s.count(needle)==1
  s=s.replace(needle, '''				require_Equal(t, ci.Name, "C")
				ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
				defer cancel()
				select {
				case <-finished:
				case <-ctx.Done(): t.Fatal("metadata handler did not retain its live-consumer request")
				}
				mjs.mu.RLock()
				retained := cc.pendingConsumerInfos
				mjs.mu.RUnlock()
				require_Equal(t, retained, int64(1))
				// Clearing the synthetic term releases that retained request.''')
 (out/name).write_text(s)
 subprocess.run(['gofmt','-w',str(out/name)],check=True)
base=json.loads((root/'work/nats-workqueue-inflight-262.json').read_text())
for c in base['cases']:
 c['name']=c['name'].replace('262','263')
 c['overlays']={str(p.relative_to(root)):'server/'+p.name for p in out.glob('*.go')}
 c['pattern']='^TestJetStream(ConsumerRecreateDuringMetaApplyLag|ConsumerInfoPendingDeleteLifecycle|ClusterConsumerInfoWithInflightConsumerDelete)$'
 c['count']=5
(root/'work/nats-workqueue-inflight-263.json').write_text(json.dumps(base,indent=2)+'\n')
