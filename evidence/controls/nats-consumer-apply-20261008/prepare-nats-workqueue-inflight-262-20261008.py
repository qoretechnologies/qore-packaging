# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import subprocess
root=Path.cwd()
prior=root/'work/nats-workqueue-inflight-261-20261008'
out=root/'work/nats-workqueue-inflight-262-20261008'
out.mkdir()
for name in ['jetstream_api.go','jetstream_cluster.go','jetstream_cluster_2_test.go']:
 s=(prior/name).read_text()
 if name=='jetstream_api.go':
  s=s.replace('// Request for information about an consumer.\n// deferConsumerInfoRequest','// deferConsumerInfoRequest')
  s=s.replace('func (s *Server) jsConsumerInfoRequest(', '// Request for information about a consumer.\nfunc (s *Server) jsConsumerInfoRequest(')
 if name=='jetstream_cluster_2_test.go':
  a=s.index('func TestJetStreamConsumerInfoPendingDeleteLifecycle(')
  b=s[a:].replace('meta.Shutdown()','meta.Shutdown()\n\t\t\tmeta.WaitForShutdown()')
  b=b.replace('''			if completion == "term_reset" || completion == "applied" {''','''			// Restore the ordinary queue capacity after checking the retained-request
			// cap: two simultaneous replays must not intentionally fill and drain
			// a queue whose test-only limit is two.
			atomic.StoreInt64(&mjs.infoQueueLimit, oldLimit)
			if completion == "term_reset" || completion == "applied" {''')
  s=s[:a]+b
 (out/name).write_text(s)
 subprocess.run(['gofmt','-w',str(out/name)],check=True)
base=json.loads((root/'work/nats-workqueue-inflight-261.json').read_text())
for c in base['cases']:
 c['name']=c['name'].replace('261','262')
 c['overlays']={str(p.relative_to(root)):'server/'+p.name for p in out.glob('*.go')}
(root/'work/nats-workqueue-inflight-262.json').write_text(json.dumps(base,indent=2)+'\n')
