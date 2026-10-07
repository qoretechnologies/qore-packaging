# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib
import json
import subprocess

source = Path('work/nats-prepared-44/nats-server-2.15.0')
output = Path('work/nats-peer-236-20261007')
output.mkdir()
filename = 'jetstream_cluster_1_test.go'
original = (source / 'server' / filename).read_text()
start = original.index('func TestJetStreamClusterPeerRemovalAPI(')
end = original.index('\nfunc ', start + 1)
function = original[start:end]
marker = '\t// Client based API'
assert function.count(marker) == 1
function = function.replace(marker, '''	// Cluster readiness counts speculative peers. Finish the last startup
	// membership commit before submitting the first removal request.
	meta := c.leader().getJetStream().getMetaGroup().(*raft)
	meta.RLock()
	var membershipIndex uint64
	if meta.membChange != nil {
		membershipIndex = meta.membChange.index
	}
	meta.RUnlock()
	if membershipIndex != 0 {
		awaitRaftProgress(t, meta, membershipIndex, 0, false)
	}

''' + marker)
path = output / filename
path.write_text(original[:start] + function + original[end:])
subprocess.run(['gofmt', '-w', str(path)], check=True)
patch = '# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n# Join the last startup membership commit before peer-removal qualification.\n'
patch += ''.join(difflib.unified_diff(original.splitlines(True), path.read_text().splitlines(True), fromfile='a/server/' + filename, tofile='b/server/' + filename))
(output / 'nats-server-peer-removal-startup-tests.patch').write_text(patch)
cases = []
for target in ['fedora', 'leap', 'el10']:
    cases.append({'name': target + '-nats-peer-236-fixed', 'target': target,
                  'count': 60, 'race': True,
                  'pattern': '^(TestJetStreamClusterPeerRemovalAPI|TestNRGUncommittedMembershipChangeOnNewLeader)$',
                  'sublist': str(source / 'server/sublist.go'),
                  'overlays': {str(path): 'server/' + filename}})
Path('work/nats-peer-236-fixed.json').write_text(json.dumps({'source': str(source), 'workers': 3, 'cases': cases}, indent=2) + '\n')
