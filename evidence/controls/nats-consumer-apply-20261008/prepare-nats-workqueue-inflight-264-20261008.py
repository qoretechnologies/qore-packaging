# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import subprocess
root=Path.cwd()
prior=root/'work/nats-workqueue-inflight-263-20261008'
out=root/'work/nats-workqueue-inflight-264-20261008'
out.mkdir()
for name in ['jetstream_api.go','jetstream_cluster.go','jetstream_cluster_2_test.go']:
 s=(prior/name).read_text()
 if name=='jetstream_api.go':
  s=s.replace('cc.qch == nil || js.shuttingDown || !cc.isLeader()', 'cc.qch == nil || js.shuttingDown || js.srv.isShuttingDown() || !cc.isLeader()')
  s=s.replace('''			if replay {
				select {''', '''			// Server shutdown steps down Raft before closing quit channels.
			// That term change must release, rather than replay, retained reads.
			if replay && !s.isShuttingDown() {
				select {''')
 (out/name).write_text(s)
 subprocess.run(['gofmt','-w',str(out/name)],check=True)
base=json.loads((root/'work/nats-workqueue-inflight-263.json').read_text())
for c in base['cases']:
 c['name']=c['name'].replace('263','264')
 c['overlays']={str(p.relative_to(root)):'server/'+p.name for p in out.glob('*.go')}
(root/'work/nats-workqueue-inflight-264.json').write_text(json.dumps(base,indent=2)+'\n')
