# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,re,subprocess,tarfile
root=Path.cwd();e=json.loads((root/'evidence/nats-create-rejection-20261008.json').read_text())
assert e['qualification']['race_enabled_results_including_subtests']==138 and e['qualification']['nonrace_full_memory_restart_results']==3
for p,h in e['files_sha256'].items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h,p
name='nats-server-stream-create-rejection.patch';assert (root/'dependencies'/name).read_bytes()==(root/'evidence/controls/nats-create-rejection-20261008'/name).read_bytes()
patches=re.findall(r'^Patch\d+: (\S+)$',(root/'dependencies/nats-server.spec').read_text(),re.M);assert len(patches)==114 and patches[-1]==name
for f,n in [('nats-candidate51-tools-tests-20261008.log',218),('nats-candidate51-runner-tests-20261008.log',7)]:
 s=(root/'results'/f).read_text();assert re.search(r'Ran '+str(n)+r' tests in [\d.]+s\n\nOK\s*$',s),f
bundle=root/'work/nats-server-candidate-51';out=root/'work/nats-prepared-51';source=out/'nats-server-2.15.0'
with (root/'results/nats-candidate51-prepare-20261008.log').open('x') as log:
 subprocess.run(['python3','-B','-W','error','tools/prepare-dependency.py','--name','nats-server','--candidate','--cache','work/nats-server-candidate-50','--output',str(bundle)],check=True,stdout=log)
out.mkdir()
with tarfile.open(bundle/'nats-server-2.15.0.tar.gz') as archive:archive.extractall(out,filter='data')
with tarfile.open(bundle/'nats-server-2.15.0-vendor.tar.xz') as archive:archive.extractall(source,filter='data')
with (root/'results/nats-candidate51-patches-20261008.log').open('x') as log:
 for patch in patches:
  r=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(bundle/patch)],cwd=source,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  log.write(r.stdout);assert r.returncode==0 and 'fuzz' not in r.stdout.lower(),(patch,r.stdout)
  if patch==name:assert 'offset' not in r.stdout.lower(),r.stdout
prev=root/'work/nats-prepared-50/nats-server-2.15.0';changes=[]
for p in source.rglob('*.go'):
 if p.is_file() and p.read_bytes()!=(prev/p.relative_to(source)).read_bytes():changes.append(str(p.relative_to(source)))
assert sorted(changes)==['server/jetstream_cluster.go','server/jetstream_cluster_2_test.go'],changes
for rel in changes:assert (source/rel).read_bytes()==(root/'work/nats-create-proposal-fix-271-20261008'/Path(rel).name).read_bytes(),rel
manifest=json.loads((bundle/'source-manifest.json').read_text())
for p,h in manifest['sources'].items():assert hashlib.sha256((bundle/p).read_bytes()).hexdigest()==h,p
old=json.loads((root/'work/nats-server-candidate-50/source-manifest.json').read_text());delta=[p for p,h in manifest['sources'].items() if h!=old['sources'].get(p)]
assert sorted(delta)==sorted([name,'nats-server.spec','nats-server.changes']),delta
record={'schema':1,'patches':114,'fuzz':0,'new_patch_offsets':0,'changed_go_files_from_candidate50':sorted(changes),'changed_bundle_files':delta,'exact_focused_source_identity':True,'qualification':'evidence/nats-create-rejection-20261008.json','source_manifest':manifest,'remaining':'The historical 250-stream and atomic-create timeouts and sparse-consumer performance gate remain open. Full combined RPM matrix, native OBS, client/module and repository lifecycle qualification are required.'}
(root/'results/nats-candidate51-patch-verification-20261008.json').write_text(json.dumps(record,indent=2)+'\n')
print('All 114 patches apply; both changed Go files exactly match the 141-result qualification.')
