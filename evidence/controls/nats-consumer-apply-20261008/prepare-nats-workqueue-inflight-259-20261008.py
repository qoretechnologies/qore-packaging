# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import subprocess

root = Path.cwd()
source = root / 'work/nats-prepared-48/nats-server-2.15.0/server'
out = root / 'work/nats-workqueue-inflight-259-20261008'
out.mkdir()
cluster = (source / 'jetstream_cluster.go').read_text()
cluster = cluster.replace('\tinflightConsumers map[string]map[string]map[string]*inflightConsumerInfo\n', '\tinflightConsumers map[string]map[string]map[string]*inflightConsumerInfo\n\t// Requests waiting for pending consumer changes to be applied; guarded by js.mu.\n\tpendingConsumerInfos int64\n')
needle = 'type inflightConsumerInfo struct {\n\tops     uint64 // Inflight operations, i.e. inflight consumer creates/updates/deletes.\n\tdeleted bool   // Whether the consumer has been deleted.\n\t*consumerAssignment\n}'
assert cluster.count(needle) == 1
cluster = cluster.replace(needle, needle[:-2] + '\n\t// Closed when these proposals finish or their metadata leadership term ends.\n\tapplied chan struct{}\n}')
cluster = cluster.replace('&inflightConsumerInfo{1, deleted, ca}', '&inflightConsumerInfo{ops: 1, deleted: deleted, consumerAssignment: ca}')
needle = '\t\t// No pending operations left, clean up.\n\t\tdelete(consumers, consumerName)'
assert cluster.count(needle) == 1
cluster = cluster.replace(needle, '\t\t// No pending operations left; wake information requests before cleanup.\n\t\tif inflight.applied != nil {\n\t\t\tclose(inflight.applied)\n\t\t}\n\t\tdelete(consumers, consumerName)')
needle = '\tjs.cluster.inflightConsumers = nil\n'
assert cluster.count(needle) == 1
cluster = cluster.replace(needle, '''	for _, streams := range js.cluster.inflightConsumers {
		for _, consumers := range streams {
			for _, inflight := range consumers {
				if inflight.applied != nil {
					close(inflight.applied)
				}
			}
		}
	}
''' + needle)
(out / 'jetstream_cluster.go').write_text(cluster)
api = (source / 'jetstream_api.go').read_text()
a = api.index('func (s *Server) jsConsumerInfoRequest(')
b = api.index('\nfunc ', a + 1)
body = api[a:b]
needle = '\t\tjs.mu.RLock()\n\t\tmeta := cc.meta\n'
assert body.count(needle) == 1
body = body.replace(needle, '''		if deferred, overloaded := js.deferConsumerInfoRequest(sub, c, acc, subject, reply, rmsg, streamName, consumerName); deferred {
			return
		} else if overloaded {
			resp.Error = NewJSClusterNotAvailError()
			s.sendAPIErrResponse(ci, acc, subject, reply, string(msg), s.jsonResponse(&resp))
			return
		}

''' + needle)
api = api[:a] + body + api[b:]
helper = '''// deferConsumerInfoRequest retains the metadata leader's request while a
// deletion is pending. The current consumer leader can still answer immediately;
// the metadata leader re-evaluates its applied state when the proposals finish.
// A pending deletion alone does not prove that the consumer has stopped.
func (js *jetStream) deferConsumerInfoRequest(sub *subscription, c *client, acc *Account, subject, reply string, rmsg []byte, stream, consumer string) (deferred, overloaded bool) {
	js.mu.Lock()
	cc := js.cluster
	if cc == nil || cc.meta == nil || cc.qch == nil || js.shuttingDown || !cc.isLeader() || cc.isConsumerLeader(acc.Name, stream, consumer) ||
		js.consumerAssignment(acc.Name, stream, consumer) == nil {
		js.mu.Unlock()
		return false, false
	}
	inflight := cc.inflightConsumers[acc.Name][stream][consumer]
	if inflight == nil || !inflight.deleted {
		js.mu.Unlock()
		return false, false
	}
	// Bound retained requests by the same configured limit as the info queue.
	if cc.pendingConsumerInfos >= atomic.LoadInt64(&js.infoQueueLimit) {
		js.mu.Unlock()
		return false, true
	}
	if inflight.applied == nil {
		inflight.applied = make(chan struct{})
	}
	applied, quit := inflight.applied, cc.qch
	cc.pendingConsumerInfos++
	atomic.AddInt64(&js.apiInflight, 1)
	js.mu.Unlock()

	// The API worker's client is reused after this callback. Keep only the
	// independent request bytes and parse state, never that mutable client.
	s := js.srv
	rmsg = copyBytes(rmsg)
	requestClient := &client{srv: s, kind: JETSTREAM}
	requestClient.pa.hdr = c.pa.hdr
	finish := func() {
		js.mu.Lock()
		cc.pendingConsumerInfos--
		js.mu.Unlock()
		atomic.AddInt64(&js.apiInflight, -1)
	}
	if !s.startGoRoutine(func() {
		defer s.grWG.Done()
		defer finish()
		select {
		case <-applied:
			// Re-enter the normal bounded queue, with fresh leadership and
			// assignment checks. No delay, polling, or stale response is used.
			js.apiDispatch(sub, requestClient, acc, subject, reply, rmsg)
		case <-quit:
		case <-s.quitCh:
		}
	}) {
		finish()
	}
	return true, false
}

'''
a = api.index('func (s *Server) jsConsumerInfoRequest(')
api = api[:a] + helper + api[a:]
(out / 'jetstream_api.go').write_text(api)
(out / 'jetstream_cluster_2_test.go').write_bytes((root / 'work/nats-workqueue-inflight-256-20261008/jetstream_cluster_2_test.go').read_bytes())
for p in out.glob('*.go'):
 subprocess.run(['gofmt', '-w', str(p)], check=True)
pattern = '^TestJetStream(ConsumerRecreateDuringMetaApplyLag|ClusterConsumerInfoWithInflightConsumerDelete|ClusterWorkQueueLosingMessagesOnConsumerDelete|ClusterConsumerInfoAfterCreate|ConsumerInfoMissingLocalStream|ConsumerInfoMissingStreamStandalone|ConsumerAssignmentInfoLifetime|ConsumerInfoBeforePreferredAssignment)$'
cases = []
for target in ['fedora', 'leap', 'el10']:
 cases.append({'name': f'{target}-nats-workqueue-inflight-259', 'target': target, 'count': 1, 'race': True, 'pattern': pattern,
  'sublist': str((source / 'sublist.go').relative_to(root)),
  'overlays': {str(p.relative_to(root)): 'server/' + p.name for p in out.glob('*.go')}})
(root / 'work/nats-workqueue-inflight-259.json').write_text(json.dumps({'source': str(source.parent.relative_to(root)), 'workers': 3, 'cases': cases}, indent=2) + '\n')
print('Prepared event-driven metadata-apply proposal with bounded request retention')
