# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib
import json
import subprocess

source = Path('work/nats-prepared-44/nats-server-2.15.0')
output = Path('work/nats-purge-237-20261007')
output.mkdir()
filename = 'jetstream_cluster_2_test.go'
original = (source / 'server' / filename).read_text()
start = original.index('func TestJetStreamClusterPurgeBySequence(')
end = original.index('\nfunc ', start + 1)
text = original[start:end]
old = '\t\t\tnc.Request(fmt.Sprintf(JSApiStreamCreateT, cfg.Name), req, time.Second)'
assert text.count(old) == 1
text = text.replace(old, '''			created, err := nc.Request(fmt.Sprintf(JSApiStreamCreateT, cfg.Name), req, time.Second)
			require_NoError(t, err)
			var createResponse JSApiStreamCreateResponse
			require_NoError(t, json.Unmarshal(created.Data, &createResponse))
			if createResponse.Error != nil {
				t.Fatalf("create response: %s", created.Data)
			}
			awaitStreamRouteInterest(t, c, nc, "KV")''')
old = '\t\t\t_, err = nc.Request(fmt.Sprintf(JSApiStreamPurgeT, "KV"), jr, time.Second)'
assert text.count(old) == 1
text = text.replace(old, '\t\t\tpurged, err := nc.Request(fmt.Sprintf(JSApiStreamPurgeT, "KV"), jr, time.Second)')
marker = '\t\t\t// 18 should still be there'
assert text.count(marker) == 1
text = text.replace(marker, '''			var purgeResponse JSApiStreamPurgeResponse
			require_NoError(t, json.Unmarshal(purged.Data, &purgeResponse))
			if purgeResponse.Error != nil {
				t.Fatalf("purge response: %s", purged.Data)
			}
			require_True(t, purgeResponse.Success)
			require_Equal(t, purgeResponse.Purged, uint64(2))

			// The leader replies after its purge; an ephemeral R1 consumer may
			// use either replica. Join follower application before creating it.
			leader := c.streamLeader(globalAccountName, "KV")
			stream, err := leader.GlobalAccount().lookupStream("KV")
			require_NoError(t, err)
			node := stream.raftNode().(*raft)
			node.RLock()
			purgeIndex := node.commit
			node.RUnlock()
			var joined int
			for _, server := range c.servers {
				if replica, err := server.GlobalAccount().lookupStream("KV"); err == nil {
					awaitRaftProgress(t, replica.raftNode().(*raft), purgeIndex, 0, false)
					joined++
				}
			}
			require_Equal(t, joined, cfg.Replicas)
''' + marker)
control = Path('work/nats-purge-replica-235-control.go.txt').read_text()
path = output / filename
path.write_text(original[:start] + text + original[end:] + '\n' + control)
subprocess.run(['gofmt', '-w', str(path)], check=True)
patch = '# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n# Join replicated purge application before arbitrary ephemeral consumer placement.\n'
patch += ''.join(difflib.unified_diff(original.splitlines(True), path.read_text().splitlines(True), fromfile='a/server/' + filename, tofile='b/server/' + filename))
(output / 'nats-server-purge-replica-completion-tests.patch').write_text(patch)
negative = output / 'negative_jetstream_cluster_2_test.go'
negative.write_text(path.read_text().replace('require_Equal(t, before.FirstSeq, uint64(16))', 'require_Equal(t, before.FirstSeq, uint64(18))'))
assert negative.read_text() != path.read_text()
for variant, overlay, count, pattern in [
    ('fixed', path, 20, '^(TestJetStreamClusterPurgeBySequence|TestRPMPurgeReplicaApplyBoundary)$'),
    ('negative', negative, 1, '^TestRPMPurgeReplicaApplyBoundary$'),
]:
    cases = [{'name': target + '-nats-purge-237-' + variant, 'target': target,
              'count': count, 'race': True, 'pattern': pattern,
              'sublist': str(source / 'server/sublist.go'),
              'overlays': {str(overlay): 'server/' + filename}}
             for target in ['fedora', 'leap', 'el10']]
    Path('work/nats-purge-237-' + variant + '.json').write_text(json.dumps({'source': str(source), 'workers': 3, 'cases': cases}, indent=2) + '\n')
