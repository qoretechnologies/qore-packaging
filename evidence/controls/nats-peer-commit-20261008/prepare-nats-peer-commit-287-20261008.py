# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib
import json
import subprocess

root = Path.cwd()
source = root / 'work/nats-prepared-54/nats-server-2.15.0'
out = root / 'work/nats-peer-commit-287-20261008'
out.mkdir()
original = (source / 'server/raft_test.go').read_text()
name = 'TestNRGLeaderResurrectsRemovedPeers'
a = original.index('func ' + name + '(')
b = original.index('\nfunc ', a + 1)
body = original[a:b]
old = '''	// Remove one follower
	require_NoError(t, leader.node().ProposeRemovePeer(followers[0].node().ID()))
	checkFor(t, 2*time.Second, 10*time.Millisecond, func() error {
		if peers := leader.node().Peers(); len(peers) == 2 {
			return nil
		}
		return errors.New("membership still in progress")
	})
'''
new = '''	// The peer map changes speculatively before the removal is committed.
	// Join committed removal before stopping a node with an in-memory WAL.
	removed := followers[0].node().ID()
	require_NoError(t, leader.node().ProposeRemovePeer(removed))
	deadline := time.NewTimer(2 * time.Second)
	defer deadline.Stop()
	require_NoError(t, awaitCommittedPeerRemoval(leader.node().(*raft), removed, deadline.C))
'''
assert body.count(old) == 1
helpers = '''// awaitCommittedPeerRemoval joins the existing application notification. The
// observer is installed before inspecting state under the same lock: completion
// before registration is seen immediately, and later completion sends progress.
// The caller supplies the original test budget; no polling or retry is needed.
func awaitCommittedPeerRemoval(n *raft, peer string, deadline <-chan time.Time) error {
	progress := make(chan struct{}, 1)
	n.Lock()
	if n.progressC != nil {
		n.Unlock()
		return errors.New("Raft progress already has an observer")
	}
	n.progressC = progress
	n.Unlock()
	defer func() { n.Lock(); n.progressC = nil; n.Unlock() }()
	for {
		n.RLock()
		_, present := n.peers[peer]
		_, removed := n.removed[peer]
		ready := !present && removed && n.membChange == nil
		n.RUnlock()
		if ready {
			return nil
		}
		select {
		case <-progress:
		case <-n.QuitC():
			return errors.New("Raft node stopped before committed peer removal")
		case <-deadline:
			return errors.New("Raft peer removal was not committed within the test budget")
		}
	}
}

func TestPackagingCommittedPeerRemovalObserver(t *testing.T) {
	expired := make(chan time.Time)
	close(expired)
	for _, row := range []struct {
		name string
		present, removed, pending, ready bool
	}{
		{"unknown", false, false, false, false},
		{"speculative", false, false, true, false},
		{"still-present", true, true, false, false},
		{"membership-pending", false, true, true, false},
		{"committed", false, true, false, true},
	} {
		t.Run(row.name, func(t *testing.T) {
			n := &raft{peers: make(map[string]*lps), removed: make(map[string]time.Time)}
			if row.present { n.peers["old-peer"] = &lps{} }
			if row.removed { n.removed["old-peer"] = time.Now() }
			if row.pending { n.membChange = &membChange{} }
			err := awaitCommittedPeerRemoval(n, "old-peer", expired)
			if row.ready {
				require_NoError(t, err)
			} else {
				require_Error(t, err, errors.New("Raft peer removal was not committed within the test budget"))
			}
			require_True(t, n.progressC == nil)
		})
	}
	t.Run("closed", func(t *testing.T) {
		n := &raft{quit: make(chan struct{})}
		close(n.quit)
		require_Error(t, awaitCommittedPeerRemoval(n, "old-peer", nil),
			errors.New("Raft node stopped before committed peer removal"))
		require_True(t, n.progressC == nil)
	})
	t.Run("existing-observer", func(t *testing.T) {
		progress := make(chan struct{}, 1)
		n := &raft{progressC: progress}
		require_Error(t, awaitCommittedPeerRemoval(n, "old-peer", expired),
			errors.New("Raft progress already has an observer"))
		require_True(t, n.progressC == progress)
	})
}

func TestPackagingPeerRemovalCommitBoundary(t *testing.T) {
	n, cleanup := initSingleMemRaftNode(t)
	defer cleanup()
	const survivor, removed = "S1Nunr6R", "yrzKKRBu"
	n.addPeer(survivor)
	n.addPeer(removed)
	n.switchToLeader()
	require_True(t, n.sendMembershipChange(newEntry(EntryRemovePeer, []byte(removed))))
	// No running Raft loop can supply a quorum in this manual-node fixture.
	// The old test's predicate succeeds while persisted membership still has 3.
	require_Equal(t, len(n.Peers()), 2)
	require_NotNil(t, n.membChange)
	ps, err := readPeerState(n.dios, n.sd)
	require_NoError(t, err)
	require_Equal(t, len(ps.knownPeers), 3)
	require_True(t, slices.Contains(ps.knownPeers, removed))
	expired := make(chan time.Time)
	close(expired)
	require_Error(t, awaitCommittedPeerRemoval(n, removed, expired),
		errors.New("Raft peer removal was not committed within the test budget"))

	// Drive the actual commit path, including the durable membership write.
	index := n.membChange.index
	for next := n.commit + 1; next <= index; next++ {
		n.Lock()
		err := n.applyCommit(next)
		n.Unlock()
		require_NoError(t, err)
		n.Applied(next)
	}
	require_NoError(t, awaitCommittedPeerRemoval(n, removed, expired))
	ps, err = readPeerState(n.dios, n.sd)
	require_NoError(t, err)
	require_Equal(t, len(ps.knownPeers), 2)
	require_False(t, slices.Contains(ps.knownPeers, removed))
	require_True(t, n.progressC == nil)
	t.Log("Speculative peer count is 2 with 3 durable peers; committed removal persists exactly 2")
}

'''
clean = original[:a] + helpers + body.replace(old, new) + original[b:]
(out / 'clean.go').write_text(clean)
subprocess.run(['gofmt', '-w', str(out / 'clean.go')], check=True)
patch = '# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n# Observe committed peer removal before the in-memory Raft restart fixture shuts down.\n'
patch += ''.join(difflib.unified_diff(original.splitlines(True), (out/'clean.go').read_text().splitlines(True), fromfile='a/server/raft_test.go', tofile='b/server/raft_test.go'))
(out/'nats-server-peer-commit-tests.patch').write_text(patch)
pattern = '^(TestNRGLeaderResurrectsRemovedPeers|TestPackagingCommittedPeerRemovalObserver|TestPackagingPeerRemovalCommitBoundary|TestNRGTruncateWALRevertsUncommittedRemovePeer|TestRaftProgressNotification)$'
cases = []
for target in ['fedora', 'leap', 'el10']:
    cases.append({'name': f'{target}-nats-peer-commit-287', 'target':target, 'count':20, 'race':True, 'pattern':pattern,
        'sublist':str((source/'server/sublist.go').relative_to(root)),
        'overlays':{str((out/'clean.go').relative_to(root)):'server/raft_test.go'}})
(root/'work/nats-peer-commit-287.json').write_text(json.dumps({'source':str(source.relative_to(root)), 'workers':3, 'cases':cases}, indent=2)+'\n')
print('Prepared committed-removal fixture, state/deadline/closed controls and durable membership regression.')
