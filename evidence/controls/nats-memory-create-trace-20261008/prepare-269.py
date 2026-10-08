# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
root=Path.cwd();src=root/'work/nats-prepared-50/nats-server-2.15.0'; prev=root/'work/nats-memory-create-trace-268-20261008';out=root/'work/nats-memory-create-trace-269-20261008';out.mkdir()
a=(src/'server/norace_2_test.go').read_text();control=(prev/'norace_2_test.go').read_text().split('func TestNoRaceRPMConcurrentMemoryCreationTrace(',1)[1]
setup=control[control.index('\tlogs :='):control.index('\n\tnc, js :=')]
start=a.index('func TestNoRaceJetStreamClusterMemoryStreamLastSequenceResetAfterRestart(');end=a.index('\nfunc ',start+1)
body=a[start:end].replace('\tdefer c.shutdown()\n','\tdefer c.shutdown()\n'+setup,1).replace('\t\t\tresults <- err\n','\t\t\tif err != nil { err=fmt.Errorf("stream TEST:%d create: %w",n,err) }\n\t\t\tresults <- err\n',1)
a=a[:start]+body+a[end:];(out/'norace_2_test.go').write_text(a)
subprocess.run(['gofmt','-w',str(out/'norace_2_test.go')],check=True)
report=json.loads((root/'results/leap-nats-server-candidate-46/rpmbuild/BUILD/nats-server-2.15.0-build/nats-server-2.15.0/nats-test-results.json').read_text())
g=next(g for g in report['groups'] if g['group']=='TestNoRace-2')
# Preserve the entire exact original group, original order is supplied by go test.
case={'name':'leap-nats-memory-create-trace-269-group','target':'leap','count':1,'race':False,'pattern':'^('+'|'.join(g['selected'])+')$','sublist':str(src.relative_to(root)/'server/sublist.go'),'overlays':{str((prev/x).relative_to(root)):'server/'+x for x in ('jetstream_api.go','jetstream_cluster.go')}}
case['overlays'][str((out/'norace_2_test.go').relative_to(root))]='server/norace_2_test.go'
(root/'work/nats-memory-create-trace-269.json').write_text(json.dumps({'source':str(src.relative_to(root)),'workers':1,'cases':[case]},indent=2)+'\n')
print('Prepared exact 73-test original group with targeted tracing only.')
