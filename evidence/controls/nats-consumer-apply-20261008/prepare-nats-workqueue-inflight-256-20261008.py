# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib
import json
import subprocess

root = Path.cwd()
source = root / 'work/nats-prepared-48/nats-server-2.15.0/server'
out = root / 'work/nats-workqueue-inflight-256-20261008'
out.mkdir()
original = (source / 'jetstream_api.go').read_text()
a = original.index('func (s *Server) jsConsumerInfoRequest(')
b = original.index('\nfunc ', a + 1)
body = original[a:b]
needle = '\t\tif sa != nil && ca == nil {\n'
assert body.count(needle) == 1
body = body.replace(needle, '''		// A consumer leader can acknowledge deletion before the meta leader
		// applies that entry locally. Honor its pending deletion instead of
		// directing this request to a consumer that has already stopped.
		if isLeader && ca != nil && js.consumerAssignmentOrInflight(acc.Name, streamName, consumerName) == nil {
			ca = nil
		}
''' + needle)
fixed = original[:a] + body + original[b:]
(out / 'api-original.go').write_text(original)
(out / 'api-fixed.go').write_text(fixed)
test = r'''// Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.
package server

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/nats-io/nats.go"
)

// A real update blocks only the metadata leader's local consumer application.
// Its Raft group continues committing, so another consumer leader can acknowledge
// deletion before that local application catches up. No production hook or
// privately fabricated assignment is used.
func TestJetStreamConsumerRecreateDuringMetaApplyLag(t *testing.T) {
	c := createJetStreamClusterExplicit(t, "WQ-META", 3)
	defer c.shutdown()
	meta := c.leader()
	require_NotNil(t, meta)
	nc, js := jsClientConnect(t, c.randomServer())
	defer nc.Close()
	_, err := js.AddStream(&nats.StreamConfig{
		Name: "TEST", Subjects: []string{"1", "2", "3", "4", "5", "6", "7", "8", "9", "10"},
		Retention: nats.WorkQueuePolicy, Replicas: 3,
	})
	require_NoError(t, err)
	awaitStreamRouteInterest(t, c, nc, "TEST")
	for _, subject := range []string{"2", "5", "7", "9"} {
		for range 10 {
			_, err := js.Publish(subject, []byte("workqueue message"))
			require_NoError(t, err)
		}
	}
	delivery, err := nc.SubscribeSync("bob")
	require_NoError(t, err)
	defer delivery.Unsubscribe()
	cfg := &nats.ConsumerConfig{Name: "test", FilterSubjects: []string{"6", "7", "8", "9", "10"},
		DeliverSubject: "bob", AckPolicy: nats.AckExplicitPolicy, AckWait: time.Minute, MaxAckPending: 1}
	created, err := js.AddConsumer("TEST", cfg)
	require_NoError(t, err)
	_, err = delivery.NextMsg(time.Second)
	require_NoError(t, err)
	awaitClusterMetaApplied(t, c)
	preferred := c.randomNonLeader()
	consumerLeader := c.consumerLeader(globalAccountName, "TEST", "test")
	require_NotNil(t, consumerLeader)
	if consumerLeader != preferred {
		elected := observePreferredElection(t, preferred, JSAdvisoryConsumerLeaderElectedPre+".TEST.test", globalAccountName, "TEST", 10*time.Second)
		stream, err := consumerLeader.GlobalAccount().lookupStream("TEST")
		require_NoError(t, err)
		consumer := stream.lookupConsumer("test")
		require_NotNil(t, consumer)
		consumer.mu.RLock()
		node := consumer.node.(*raft)
		consumer.mu.RUnlock()
		peer := preferred.getJetStream().getMetaGroup().ID()
		awaitPreferredPeer(t, node, peer)
		require_NoError(t, node.StepDown(peer))
		elected()
	}
	require_True(t, c.consumerLeader(globalAccountName, "TEST", "test") != meta)
	require_True(t, c.leader() == meta)
	stream, err := meta.GlobalAccount().lookupStream("TEST")
	require_NoError(t, err)
	consumer := stream.lookupConsumer("test")
	require_NotNil(t, consumer)
	consumer.mu.Lock()
	var unlocked sync.Once
	unblock := func() { unlocked.Do(consumer.mu.Unlock) }
	defer unblock()
	updated := *cfg
	updated.AckWait = 2 * time.Minute
	_, err = js.UpdateConsumer("TEST", &updated)
	require_NoError(t, err)
	require_NoError(t, js.DeleteConsumer("TEST", "test"))
	// Prove this is an acknowledged real delete, still unapplied on the meta
	// leader, and not a constructed copy of a completed create assignment.
	mjs := meta.getJetStream()
	mjs.mu.RLock()
	applied := mjs.consumerAssignment(globalAccountName, "TEST", "test")
	inflight := mjs.consumerAssignmentOrInflight(globalAccountName, "TEST", "test")
	mjs.mu.RUnlock()
	require_NotNil(t, applied)
	require_True(t, inflight == nil)

	// Observe completion of each real information handler without altering it.
	infoSubject := fmt.Sprintf(JSApiConsumerInfoT, "TEST", "test")
	finished := make(chan *Server, 8)
	var observing atomic.Bool
	observing.Store(true)
	for _, server := range c.servers {
		api := server.getJetStream().apiSubs
		matched := api.Match(infoSubject).psubs
		require_Equal(t, len(matched), 1)
		original := matched[0]
		replacement := &subscription{subject: append([]byte(nil), original.subject...),
			icb: func(sub *subscription, client *client, account *Account, subject, reply string, msg []byte) {
				original.icb(sub, client, account, subject, reply, msg)
				if subject == infoSubject && observing.Load() {
					finished <- server
				}
			}}
		require_NoError(t, api.Remove(original))
		require_NoError(t, api.Insert(replacement))
		defer func() { require_NoError(t, api.Remove(replacement)); require_NoError(t, api.Insert(original)) }()
	}
	requests := make(chan string, 8)
	traced, err := nc.JetStream(nats.MaxWait(10*time.Second), nats.ClientTrace{
		RequestSent: func(subject string, _ []byte) { requests <- subject },
	})
	require_NoError(t, err)
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	type result struct { info *nats.ConsumerInfo; err error }
	completed := make(chan result, 1)
	var workers sync.WaitGroup
	workers.Add(1)
	defer func() { cancel(); workers.Wait() }()
	go func() {
		defer workers.Done()
		info, err := traced.AddConsumer("TEST", cfg, nats.Context(ctx))
		completed <- result{info, err}
	}()
	seen := make(map[*Server]bool)
	for len(seen) < len(c.servers) {
		select {
		case server := <-finished:
			seen[server] = true
		case <-ctx.Done():
			t.Fatal("information request did not finish on all three handlers")
		}
	}
	observing.Store(false)
	unblock()
	recreated := <-completed
	var sent []string
	for len(requests) > 0 { sent = append(sent, <-requests) }
	t.Logf("acknowledged delete with lagging metadata; AddConsumer requests: %v", sent)
	require_NoError(t, recreated.err)
	require_NotNil(t, recreated.info)
	require_True(t, recreated.info.Created.After(created.Created))
	require_Equal(t, len(sent), 2)
	require_Equal(t, sent[0], infoSubject)
	require_Equal(t, sent[1], "$JS.API.CONSUMER.CREATE.TEST.test")
	previous := recreated.info.Created
	for range 4 {
		message, err := delivery.NextMsg(time.Second)
		require_NoError(t, err)
		require_Equal(t, string(message.Data), "workqueue message")
		require_NoError(t, js.DeleteConsumer("TEST", "test"))
		next, err := js.AddConsumer("TEST", cfg)
		require_NoError(t, err)
		require_True(t, next.Created.After(previous))
		previous = next.Created
	}
	info, err := js.StreamInfo("TEST")
	require_NoError(t, err)
	require_Equal(t, info.State.Msgs, uint64(40))
}
'''
test = (source / 'jetstream_cluster_2_test.go').read_text() + '\n' + test[test.index('// A real update'): ]
(out / 'jetstream_cluster_2_test.go').write_text(test)
for p in out.glob('*.go'):
    subprocess.run(['gofmt', '-w', str(p)], check=True)
fixed = (out / 'api-fixed.go').read_text()
patch = '# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n'
patch += '# Honor inflight deletion when answering consumer information from the metadata leader.\n'
patch += ''.join(difflib.unified_diff(original.splitlines(True), fixed.splitlines(True), fromfile='a/server/jetstream_api.go', tofile='b/server/jetstream_api.go'))
(out / 'nats-server-consumer-info-inflight-delete.patch').write_text(patch)
cases = []
for variant in ['original', 'fixed']:
    for target in ['fedora', 'leap', 'el10']:
        cases.append({'name': f'{target}-nats-workqueue-inflight-256-{variant}', 'target': target,
                      'count': 1, 'race': True, 'pattern': '^TestJetStreamConsumerRecreateDuringMetaApplyLag$',
                      'sublist': str((source / 'sublist.go').relative_to(root)),
                      'overlays': {str((out / f'api-{variant}.go').relative_to(root)): 'server/jetstream_api.go',
                                   str((out / 'jetstream_cluster_2_test.go').relative_to(root)): 'server/jetstream_cluster_2_test.go'}})
(root / 'work/nats-workqueue-inflight-256.json').write_text(json.dumps({
    'source': str(source.parent.relative_to(root)), 'workers': 3, 'cases': cases}, indent=2) + '\n')
print('Prepared real update/delete/recreate lifecycle regression and minimal inflight-delete proposal')
