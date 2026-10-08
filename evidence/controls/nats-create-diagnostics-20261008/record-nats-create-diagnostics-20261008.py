# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip, hashlib, importlib.util, json, re, shutil
root=Path.cwd();out=root/'evidence/controls/nats-create-diagnostics-20261008';out.mkdir()
records=[]
for version,count in [(283,51),(284,17)]:
 for target in ['fedora','leap','el10']:
  for kind,expected in [('controls',count),('memory',1)]:
   p=root/f'results/{target}-nats-create-diagnostics-{version}-{kind}'
   status=json.loads((p/'status.json').read_text());log=(p/'tests.log').read_text()
   passed=len(re.findall(r'(?m)^\s*--- PASS:',log))
   assert status['exit_code']==0 and passed==expected
   assert not re.search(r'(?m)^\s*--- (FAIL|SKIP):|WARNING: DATA RACE|panic:',log)
   dest=out/p.name;dest.mkdir()
   shutil.copy2(p/'status.json',dest/'status.json')
   (dest/'tests.log.gz').write_bytes(gzip.compress(log.encode(),mtime=0))
   records.append({'version':version,'target':target,'kind':kind,'pass':passed,'race':kind=='controls'})
for p in ['integrate-nats-create-diagnostics-20261008.py','prepare-nats-candidate53-20261008.py','record-nats-create-diagnostics-20261008.py','run-nats-focused-38.py','nats-create-diagnostics-284.json']:
 shutil.copy2(root/'work'/p,out/p)
for p in ['nats-server-create-diagnostics-tests.patch','nats-server.spec','nats-server.rst']:shutil.copy2(root/'dependencies'/p,out/p)
for p in ['jetstream_batching_test.go','norace_2_test.go']:
 (out/(p+'.gz')).write_bytes(gzip.compress((root/'work/nats-create-diagnostics-284-20261008'/p).read_bytes(),mtime=0))
for name in ['patch-verification','patches','prepare','tools-tests','runner-tests']:
 suffix='.json' if name=='patch-verification' else '.log'
 p=root/f'results/nats-candidate53-{name}-20261008{suffix}'
 if suffix=='.log':(out/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
 else:shutil.copy2(p,out/p.name)
loader=importlib.util.spec_from_file_location('audit',root/'work/write-scoped-audit.py');audit=importlib.util.module_from_spec(loader);loader.loader.exec_module(audit)
passes={9:'New code and records carry 2026 copyright; upstream notices remain.',53:'Test-only observation delegates the real callback and preserves deadlines, workloads and outcomes. No production change or skipped check.',54:'Cleanup is registered before setup; restoration runs once in reverse order. An insertion error is reported without aborting later cleanup.',55:'Existing logger mutex, JetStream lock and atomic logging fields protect observations; Raft access happens outside the JetStream lock. Final race controls pass.',56:'Go callback signatures and typed state fields are preserved. Nil assignment/group and missing-cluster observations are handled.',57:'Each server log is capped at 10,000 entries; the negative capacity test verifies 2,000 discarded events after 12,000 concurrent writes. Collection ends after creation.',58:'Real request failures remain fatal and include the stream name. Observers do not retry or manufacture a response; cleanup reports restoration failures.',59:'Dependency guide documents observation boundaries and remaining historical root-cause limits.',61:'Only isolated test-server state is logged, with bounded records and no credentials. No production I/O or API surface changes.',62:'Final 51 race-enabled and three complete memory-workload results pass; tests verify real callback entry, absent/present assignments, replica counts, exact callback restoration and subsequent creation. All 116 patches apply without fuzz and the two resulting test files match qualified sources.'}
audit.write(out/'audit.rst','NATS creation diagnostics audit','Scope: test-only creation observer and candidate53 preparation. All 62 checks: 10 Pass, 52 N/A, 0 Fail. Historical creation timeouts remain unproven; full packaging qualification remains open.',passes,'No corresponding Qore module, QPP, DataProvider, JNI, C++ production or Qore-language test change in this scope.')
record={'schema':1,'date':'2026-10-08','copyright':'Copyright 2026 Qore Technologies, s.r.o.','status':'Test-only diagnostics qualified; candidate53 prepared for complete RPM matrix. Historical untraced creation timeouts are not claimed fixed.','patch':'Patch115: nats-server-create-diagnostics-tests.patch','qualification':records,'final_results':54,'final_race_results':51,'preliminary_results':156,'packaging_tests':225,'patches':116,'source_sha256':{p:hashlib.sha256((root/'work/nats-create-diagnostics-284-20261008'/p).read_bytes()).hexdigest() for p in ['jetstream_batching_test.go','norace_2_test.go']},'limits':['Per-server snapshots are not an atomic cluster view. Callback return does not establish reply delivery.','No new runtime change, deadline increase, retry, result override or warning suppression.','Candidate283 passed; candidate284 additionally preserves all restorations after an error and tolerates a missing group in diagnostics.','The first packaging runner invocation imported its tests without executing them; the preparation guard rejected its empty report. Correct unittest discovery then ran all seven tests successfully.','Full combined RPM and native architectures, installed clients/modules, repository lifecycle/signing/publication remain required.'],'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}}
(root/'evidence/nats-create-diagnostics-20261008.json').write_text(json.dumps(record,indent=2)+'\n')
print('Recorded all 54 final and 156 preliminary results, 225 packaging tests, exact candidate53 identity and complete audit.')
