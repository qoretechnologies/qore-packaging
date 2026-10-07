# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import collections,gzip,hashlib,json,re,runpy,shutil
root=Path.cwd();build=root/'results/leap-nodejs24-canonical-final-20261007';memory=root/'results/node-canonical-final-memory-20261007';out=root/'evidence/controls/node-canonical-final-20261007';out.mkdir(exist_ok=True)
meta=json.loads((build/'build.json').read_text());assert meta['exit_code']==0
candidate=json.loads((root/'work/nodejs24-libnode-canonical-final-20261007/source-manifest.json').read_text());assert meta['source']==candidate
assert candidate['commit']=='a91f31028787e9b32e66de0f6dc0e340d75c8aac' and not candidate.get('candidate')
for name,digest in candidate['sources'].items():
 p=root/'dependencies'/name
 if p.is_file():assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,name
for name,digest in meta['artifacts'].items():assert hashlib.sha256((build/name).read_bytes()).hexdigest()==digest,name
text=(build/'build.log').read_text();assert '[==========] 192 tests from 31 test suites ran.' in text
assert len(re.findall(r'^ok \d+ ',text,re.M))==5249 and not re.search(r'^not ok ',text,re.M)
rx=re.compile(r'^(?:\.\./)?(.+?):(\d+):\d+: warning:.*?\[(-W[^]]+)\]$',re.M)
old=(root/'results/leap-nodejs24-obs-flags-candidate10-20261007/build.log').read_text()
assert {m[0] for m in rx.finditer(text)}=={m[0] for m in rx.finditer(old)}
qualified=json.loads((root/'work/node-candidate10-warning-context-verified-20261007.json').read_text());assert len(qualified['diagnostics'])==571
assert all(r['status'].startswith(('approved','reviewed under approved')) and r['evidence'] for r in qualified['diagnostics'])
records=json.loads((memory/'status.json').read_text());expected={'wasm-deopt':0,'reschedule':0,'timezone':0,'external-ordinary':99,'external-shared':99};assert {r['name']:r['exit_code'] for r in records}==expected
approval=json.loads((root/'evidence/node-external-string-fix-20261007.json').read_text())['requested_exception'];assert approval['status']=='approved'
retention=[]
for row in records:
 name=row['name'];vg=(memory/(name+'-valgrind.log')).read_text();output=(memory/(name+'.log')).read_text()
 if name.startswith('external-'):
  assert 'PASS: 400 native string lifetimes, both encodings and storage modes; 400 resources disposed' in output
  for kind in ('definitely lost','indirectly lost','possibly lost'):assert re.search(kind+r': 0 bytes in 0 blocks',vg)
  assert 'still reachable: 216 bytes in 6 blocks' in vg and 'ERROR SUMMARY: 6 errors from 6 contexts (suppressed: 0 from 0)' in vg
  parts=re.findall(r'==\d+== (\d+) bytes in (\d+) blocks are still reachable in loss record \d+ of 6\n(.*?)(?=\n==\d+== \n|\Z)',vg,re.S)
  assert len(parts)==6
  sites=[]
  for size,blocks,stack in parts:
   functions=[fn for fn in ('ThreadIsolation::Initialize','HeapRegistry::RegisterHeap','CodeRangeAddressHint::NotifyFreedCodeRange') if fn in stack];assert len(functions)==1,stack
   sites.append((int(size),int(blocks),functions[0]))
  assert sorted(sites)==sorted([(8,1,'ThreadIsolation::Initialize'),(48,1,'ThreadIsolation::Initialize'),(8,1,'HeapRegistry::RegisterHeap'),(8,1,'CodeRangeAddressHint::NotifyFreedCodeRange'),(40,1,'CodeRangeAddressHint::NotifyFreedCodeRange'),(104,1,'CodeRangeAddressHint::NotifyFreedCodeRange')]),sites
  retention.append({'name':name,'raw_exit_code':99,'sites':sites,'approval':'evidence/node-external-string-fix-20261007.json'})
 else:
  assert 'All heap blocks were freed -- no leaks are possible' in vg and 'ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)' in vg
 for suffix in ('.log','-valgrind.log'):shutil.copy2(memory/(name+suffix),out/(name+suffix))
(out/'build.log.gz').write_bytes(gzip.compress((build/'build.log').read_bytes(),mtime=0));shutil.copy2(build/'build.json',out/'build.json');shutil.copy2(memory/'status.json',out/'memory-status.json');shutil.copy2(root/'work/node-candidate10-warning-context-verified-20261007.json',out/'warning-review.json')
record={'schema':1,'date':'2026-10-07','status':'Committed canonical Node RPM, native memory controls, exact compiler review and installed Qore/V8 checks pass. Native OBS qualification remains required.','tests':{'native':192,'javascript_reported_results_including_upstream_skips':5249,'additional_wasm_deoptimization_scripts':31,'native_memory_controls':5,'string_resources_created_and_disposed':800,'unclassified_memory_errors':0,'lost_allocations':0},'compiler_review':dict(collections.Counter(r['status'] for r in qualified['diagnostics'])),'accepted_retention':retention,'limits':['The raw memory driver exits nonzero because --errors-for-leak-kinds=all reports the six already-approved process-lifetime allocations. This report preserves raw exits and verifies exact sizes, block counts and owning functions.','No warning or memory suppression was introduced. Native ARM and complete repository lifecycle remain publication gates.','Installed Qore/V8 checks use the exact canonical local RPMs. Native OBS x86_64/aarch64 artifacts still require qualification.'],'source':candidate,'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}}
installed=root/'results/leap-v8-node-canonical-final-installed-20261007'
installed_status=json.loads((installed/'status.json').read_text())
assert installed_status['exit_code']==0 and all(row['exit_code']==0 for row in installed_status['steps'])
prior_installed=root/'results/leap-v8-node10-installed-20261007'
for name in ('sdk-consumer','runtime-tests'):
 current=(installed/(name+'.log')).read_text()
 previous=(prior_installed/(name+'.log')).read_text()
 def diagnostics(text):
  return {re.sub(r'\(node:\d+\)', '(node:PID)', line) for line in text.splitlines() if re.search(r'(?i)warning|^error:',line)}
 assert diagnostics(current)==diagnostics(previous),(name,diagnostics(current)-diagnostics(previous))
 if name=='runtime-tests':
  rx_counts=r'Ran (\d+) test cases, (\d+) succeeded \((\d+) assertions\)'
  counts=re.findall(rx_counts,current)
  assert counts and counts==re.findall(rx_counts,previous)
  assert all(cases==passed for cases,passed,assertions in counts)
  record['tests']['installed_bridge_cases']=sum(int(row[0]) for row in counts)
  record['tests']['installed_bridge_assertions']=sum(int(row[2]) for row in counts)
for p in installed.iterdir():
 if p.is_file() and p.suffix in ('.json','.log'):shutil.copy2(p,out/('installed-'+p.name))
record['installed']=installed_status
record['files_sha256']={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
(root/'evidence/node-canonical-final-20261007.json').write_text(json.dumps(record,indent=2)+'\n')
print('Qualified canonical Node; exact compiler, five memory and installed bridge controls pass')
