# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib, json, re, subprocess, tarfile
root=Path.cwd()
for name,count in [('tools',218),('runner',7)]:
 log=(root/f'results/nats-candidate53-{name}-tests-20261008.log').read_text()
 assert re.search(r'Ran '+str(count)+r' tests in [\d.]+s\n\nOK\s*$',log)
patches=re.findall(r'^Patch\d+: (\S+)$',(root/'dependencies/nats-server.spec').read_text(),re.M)
assert len(patches)==116 and patches[-1]=='nats-server-create-diagnostics-tests.patch'
bundle=root/'work/nats-server-candidate-53';out=root/'work/nats-prepared-53';source=out/'nats-server-2.15.0'
with (root/'results/nats-candidate53-prepare-20261008.log').open('x') as log:
 subprocess.run(['python3','-B','-W','error','tools/prepare-dependency.py','--name','nats-server','--candidate','--cache','work/nats-server-candidate-52','--output',str(bundle)],check=True,stdout=log)
out.mkdir()
with tarfile.open(bundle/'nats-server-2.15.0.tar.gz') as archive:archive.extractall(out,filter='data')
with tarfile.open(bundle/'nats-server-2.15.0-vendor.tar.xz') as archive:archive.extractall(source,filter='data')
with (root/'results/nats-candidate53-patches-20261008.log').open('x') as log:
 for name in patches:
  r=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(bundle/name)],cwd=source,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  log.write(r.stdout);assert r.returncode==0 and 'fuzz' not in r.stdout.lower(),(name,r.stdout)
  if name==patches[-1]:assert 'offset' not in r.stdout.lower(),r.stdout
previous=root/'work/nats-prepared-52/nats-server-2.15.0'
changes=sorted(str(p.relative_to(source)) for p in source.rglob('*.go') if p.is_file() and p.read_bytes()!=(previous/p.relative_to(source)).read_bytes())
assert changes==['server/jetstream_batching_test.go','server/norace_2_test.go'],changes
for rel in changes:assert (source/rel).read_bytes()==(root/'work/nats-create-diagnostics-284-20261008'/Path(rel).name).read_bytes()
manifest=json.loads((bundle/'source-manifest.json').read_text())
for name,expected in manifest['sources'].items():assert hashlib.sha256((bundle/name).read_bytes()).hexdigest()==expected,name
old=json.loads((root/'work/nats-server-candidate-52/source-manifest.json').read_text())
delta=sorted(p for p,h in manifest['sources'].items() if h!=old['sources'].get(p))
assert delta==sorted([patches[-1],'nats-server.spec','nats-server.changes']),delta
record={'schema':1,'patches':116,'fuzz':0,'new_patch_offsets':0,'changed_go_files_from_candidate52':changes,'changed_bundle_files':delta,'exact_focused_source_identity':True,'source_manifest':manifest,'remaining':'Historical creation root causes, full combined RPM/native builds, installed client/module and repository qualification remain open.'}
(root/'results/nats-candidate53-patch-verification-20261008.json').write_text(json.dumps(record,indent=2)+'\n')
print('All 116 patches apply without fuzz; only two test files differ from candidate52 and match final focused qualification.')
