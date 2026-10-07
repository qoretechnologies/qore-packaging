# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib
import json
import subprocess

source = Path('work/nats-prepared-44/nats-server-2.15.0')
output = Path('work/nats-snapshot-240-20261007')
output.mkdir(exist_ok=True)
filename = 'norace_1_test.go'
original = (source / 'server' / filename).read_text()
start = original.index('func TestNoRaceJetStreamAccountLimitsAndRestartForceSnapshot(')
end = original.index('\nfunc ', start + 1)
text = original[start:end]
marker = '\tc.waitOnStreamLeader("$JS", "TEST")\n'
assert text.count(marker) == 1
text = text.replace(marker, marker + '''
	// A leader election does not finish the restarted follower's snapshot
	// transfer. Join that applied index before comparing replica contents.
	leader := c.streamLeader("$JS", "TEST")
	account, err := leader.lookupAccount("$JS")
	require_NoError(t, err)
	stream, err := account.lookupStream("TEST")
	require_NoError(t, err)
	node := stream.raftNode().(*raft)
	node.RLock()
	committed := node.commit
	node.RUnlock()
	for _, server := range c.servers {
		account, err := server.lookupAccount("$JS")
		require_NoError(t, err)
		stream, err := account.lookupStream("TEST")
		require_NoError(t, err)
		awaitRaftProgress(t, stream.raftNode().(*raft), committed, 0, false)
	}
''')
path = output / filename
path.write_text(original[:start] + text + original[end:])
subprocess.run(['gofmt', '-w', str(path)], check=True)
patch = '# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n# Finish snapshot application before comparing restored replica contents.\n'
patch += ''.join(difflib.unified_diff(original.splitlines(True), path.read_text().splitlines(True), fromfile='a/server/' + filename, tofile='b/server/' + filename))
(output / 'nats-server-snapshot-application-tests.patch').write_text(patch)

# Diagnostic-only overlay, excluded from the proposed patch.
cluster = (source / 'server/jetstream_cluster.go').read_text()
start = cluster.index('func (mset *stream) processSnapshot(')
end = cluster.index('\nfunc ', start + 1)
text = cluster[start:end]
marker = '\ts.sendInternalMsgLocked(subject, reply, nil, b)'
assert text.count(marker) == 1
text = text.replace(marker, '''	interest := s.SystemAccount().sl.Match(subject)
	fmt.Printf("SYNC-TRACE request server=%q at=%d subject=%q reply=%q psubs=%d qsubs=%d attempt=%d\\n", s.Name(), time.Now().UnixMilli(), subject, reply, len(interest.psubs), len(interest.qsubs), numRetries)
''' + marker)
marker = '\t\tcase <-notActive.C:\n\t\t\tif mrecs'
assert text.count(marker) == 1
text = text.replace(marker, '\t\tcase <-notActive.C:\n\t\t\tfmt.Printf("SYNC-TRACE inactive server=%q at=%d attempt=%d\\n", s.Name(), time.Now().UnixMilli(), numRetries)\n\t\t\tif mrecs')
trace = output / 'trace_jetstream_cluster.go'
trace.write_text(cluster[:start] + text + cluster[end:])
subprocess.run(['gofmt', '-w', str(trace)], check=True)
for variant, overlays in [
    ('trace', {str(path): 'server/' + filename, str(trace): 'server/jetstream_cluster.go'}),
    ('fixed', {str(path): 'server/' + filename}),
]:
    cases = [{'name': target + '-nats-snapshot-240-' + variant, 'target': target,
              'count': 10, 'race': False,
              'pattern': '^TestNoRaceJetStreamAccountLimitsAndRestartForceSnapshot$',
              'sublist': str(source / 'server/sublist.go'), 'overlays': overlays}
             for target in ['fedora', 'leap', 'el10']]
    Path('work/nats-snapshot-240-' + variant + '.json').write_text(json.dumps({'source': str(source), 'workers': 3, 'cases': cases}, indent=2) + '\n')
