# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib, json, re
root=Path.cwd()
source=root/'work/nats-prepared-52/nats-server-2.15.0'
fixed=root/'work/nats-create-diagnostics-284-20261008'
for target in ['fedora','leap','el10']:
 for kind,passes in [('controls',17),('memory',1)]:
  p=root/f'results/{target}-nats-create-diagnostics-284-{kind}'
  assert json.loads((p/'status.json').read_text())['exit_code']==0
  text=(p/'tests.log').read_text()
  assert len(re.findall(r'(?m)^\s*--- PASS:',text))==passes
  assert not re.search(r'(?m)^\s*--- (FAIL|SKIP):|WARNING: DATA RACE|panic:',text)
name='nats-server-create-diagnostics-tests.patch'
patch='# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n# Record bounded creation callback and assignment diagnostics without changing results or deadlines.\n'
for filename in ['jetstream_batching_test.go','norace_2_test.go']:
 patch+=''.join(difflib.unified_diff((source/'server'/filename).read_text().splitlines(True),(fixed/filename).read_text().splitlines(True),fromfile='a/server/'+filename,tofile='b/server/'+filename))
(root/'dependencies'/name).write_text(patch)
p=root/'dependencies/nats-server.spec';s=p.read_text();anchor='Patch114: nats-server-memory-subject-sequences.patch\n';assert s.count(anchor)==1
s=s.replace(anchor,anchor+'Patch115: '+name+'\n')
anchor='%changelog\n* Thu Oct 08 2026 David Nichols <david@qore.org> - 2.15.0-1.qore\n';assert s.count(anchor)==1
s=s.replace(anchor,anchor+'- Retain bounded API and assignment context for stream-creation test failures.\n- Restore original API callbacks and logging after creation, with race-tested controls.\n');p.write_text(s)
p=root/'dependencies/sources.json';s=json.loads(p.read_text());assert name not in s['nats-server']['extra_sources'];s['nats-server']['extra_sources'].append(name);p.write_text(json.dumps(s,indent=2)+'\n')
p=root/'dependencies/nats-server.rst';s=p.read_text();assert 'Candidate 52 combines upstream 2.15.0 with 115 patches.' in s
s=s.replace('Candidate 52 combines upstream 2.15.0 with 115 patches.','Candidate 53 combines upstream 2.15.0 with 116 patches.')
s+='''
Stream-creation failure context
-------------------------------

The atomic-batch and 250-stream restart tests now record bounded real API
callback entry/return and existing server diagnostics during creation. A failed
test also records assignment and Raft state under the owning locks. Original
callbacks and logging are restored after creation and during failure cleanup.
The observer changes no request result, timeout, retry policy or workload.
Snapshots are per-server observations, not an atomic cluster snapshot or proof
that a reply reached its client.

All 54 final focused results pass across the three distributions, including
51 race-enabled results and each complete 250-stream restart workload. Earlier
controls passed another 156 results. These controls qualify the observer; they
do not establish the cause of the historical untraced creation timeouts. The
complete combined build must still pass, and any new failure retains context
for diagnosis. See ``evidence/nats-create-diagnostics-20261008.json``.
''';p.write_text(s)
print('Integrated test-only Patch115; final observer passes 54 focused results.')
