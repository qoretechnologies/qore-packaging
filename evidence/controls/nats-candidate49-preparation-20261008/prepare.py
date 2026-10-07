# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tarfile

root=Path.cwd()
evidence=json.loads((root/'evidence/nats-consumer-apply-20261008.json').read_text())
assert evidence['qualification']['race_enabled_results_including_subtests']==246
for relative,digest in evidence['files_sha256'].items():
 assert hashlib.sha256((root/relative).read_bytes()).hexdigest()==digest,relative
name='nats-server-consumer-info-apply.patch'
qualified=root/'evidence/controls/nats-consumer-apply-20261008'/name
assert (root/'dependencies'/name).read_bytes()==qualified.read_bytes()
patches=re.findall(r'^Patch\d+: (\S+)$',(root/'dependencies/nats-server.spec').read_text(),re.M)
assert len(patches)==112 and patches[-1]==name
for filename,count in [('nats-candidate49-tools-tests-20261008.log',218),('nats-candidate49-runner-tests-20261008.log',7)]:
 text=(root/'results'/filename).read_text()
 assert re.search(r'Ran '+str(count)+r' tests in [\d.]+s\n\nOK\s*$',text),filename
bundle=root/'work/nats-server-candidate-49'
out=root/'work/nats-prepared-49'
source=out/'nats-server-2.15.0'
with (root/'results/nats-candidate49-prepare-20261008.log').open('x') as log:
 subprocess.run(['python3','-B','-W','error','tools/prepare-dependency.py','--name','nats-server','--candidate','--cache','work/nats-server-candidate-48','--output',str(bundle)],check=True,stdout=log)
out.mkdir()
with tarfile.open(bundle/'nats-server-2.15.0.tar.gz') as archive: archive.extractall(out,filter='data')
with tarfile.open(bundle/'nats-server-2.15.0-vendor.tar.xz') as archive: archive.extractall(source,filter='data')
with (root/'results/nats-candidate49-patches-20261008.log').open('x') as log:
 for patch in patches:
  result=subprocess.run(['patch','--batch','--fuzz=0','-p1','-i',str(bundle/patch)],cwd=source,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  log.write(result.stdout)
  assert result.returncode==0 and 'fuzz' not in result.stdout.lower(),(patch,result.stdout)
  if patch==name: assert 'offset' not in result.stdout.lower()
previous=root/'work/nats-prepared-48/nats-server-2.15.0'
changes=[]
for path in source.rglob('*.go'):
 if path.is_file():
  relative=str(path.relative_to(source))
  if path.read_bytes()!=(previous/relative).read_bytes(): changes.append(relative)
assert sorted(changes)==['server/jetstream_api.go','server/jetstream_cluster.go','server/jetstream_cluster_2_test.go'],changes
for relative in changes:
 assert (source/relative).read_bytes()==(root/'work/nats-workqueue-inflight-264-20261008'/Path(relative).name).read_bytes(),relative
manifest=json.loads((bundle/'source-manifest.json').read_text())
for relative,digest in manifest['sources'].items():
 assert hashlib.sha256((bundle/relative).read_bytes()).hexdigest()==digest,relative
old=json.loads((root/'work/nats-server-candidate-48/source-manifest.json').read_text())
delta=[n for n,h in manifest['sources'].items() if h!=old['sources'].get(n)]
assert sorted(delta)==sorted([name,'nats-server.spec','nats-server.changes']),delta
record={'schema':1,'patches':112,'fuzz':0,'new_patch_offsets':0,'changed_go_files_from_candidate48':sorted(changes),
 'changed_bundle_files':delta,'exact_focused_source_identity':True,'qualification':'evidence/nats-consumer-apply-20261008.json','source_manifest':manifest,
 'remaining':'Review complete candidate46 matrix before the combined full build; historical sparse performance and atomic-batch creation, native OBS, client/module and repository lifecycle gates remain.'}
(root/'results/nats-candidate49-patch-verification-20261008.json').write_text(json.dumps(record,indent=2)+'\n')
print('All 112 patches apply; the three changed Go files exactly match the 246-result qualification')
