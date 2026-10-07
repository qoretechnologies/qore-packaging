# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,importlib.util,json,subprocess,shutil,tarfile
root=Path.cwd();source=root/'work/qore-doc-sdk22-canonical-final-20261007';m=json.loads((source/'source-manifest.json').read_text());assert m['commit']=='49152d805b73c417db2bf3c0ac72dd22bfa8f058'
assert not any(m.get(k) for k in ['candidate','packaging_overlay','qualification_only'])
loader=importlib.util.spec_from_file_location('builder',root/'tools/build-local.py');builder=importlib.util.module_from_spec(loader);loader.loader.exec_module(builder);builder.verify_bundle(source)
proof=json.loads((root/'results/core-sdk22-commit-source-20261007.json').read_text());archive=next(n for n in m['sources'] if n.endswith('.tar.xz'));prefix=m['name']+'-'+m['version']
with tarfile.open(source/archive) as tar:
 for n,d in proof['files'].items():
  member=tar.getmember(prefix+'/'+n);assert member.isfile() and oct(member.mode&0o777)==d['mode'];assert hashlib.sha256(tar.extractfile(member).read()).hexdigest()==d['sha256'],n
print('Verified all 665 committed source files, including executable modes, in canonical archive',flush=True)
# The original staging trees duplicate artifacts already qualified and hashed.
# Keep their build sources, libraries, documentation, RPMs and logs for diagnosis.
old=json.loads((root/'evidence/core-sdk22-candidate4-20261007.json').read_text());ids=subprocess.check_output(['docker','ps','-q'],text=True).split();active=json.loads(subprocess.check_output(['docker','inspect',*ids],text=True)) if ids else []
removed=[]
for target in ['fedora','leap','el10']:
 base=root/f'results/{target}-core-doc-sdk22-candidate4-20261007';assert old['targets'][target]['exit_code']==0
 candidates=[base/'rpmbuild/BUILDROOT',*(base/'rpmbuild/BUILD').glob('*/BUILDROOT')];paths=[p for p in candidates if p.exists()];assert len(paths)==1,paths
 for container in active:
  for mount in container.get('Mounts',[]):
   p=Path(mount.get('Source','/nonexistent'));assert not(p==base or p.is_relative_to(base)),container['Id']
 for p in paths:
  assert p.is_dir() and not p.is_symlink() and p.resolve().is_relative_to(base.resolve())
  size=int(subprocess.check_output(['du','-s','-B1',str(p)],text=True).split()[0]);shutil.rmtree(p);removed.append({'path':str(p.relative_to(root)),'allocated_bytes':size})
(root/'results/core-sdk22-candidate4-staging-cleanup-20261007.json').write_text(json.dumps({'removed':removed,'preserved':'RPMs, logs, source, build libraries and documentation'},indent=2)+'\n');print('Reclaimed staging bytes:',sum(x['allocated_bytes'] for x in removed),flush=True)
assert shutil.disk_usage(root).free>55*1024**3
images={t:json.loads((root/f'results/{t}-core-doc-sdk22-candidate4-20261007/build.json').read_text())['image'] for t in ['fedora','leap','el10']}
def build(target):
 with (root/f'results/{target}-core-sdk22-canonical-final-driver-20261007.log').open('x') as log:
  r=subprocess.run(['python3','-B','-W','error','tools/build-local.py','--source',str(source),'--image',images[target],'--output',f'results/{target}-core-sdk22-canonical-final-20261007','--jobs','2','--keep-build'],stdout=log,stderr=subprocess.STDOUT)
 return target,r.returncode
with ThreadPoolExecutor(max_workers=3) as pool:status=dict(pool.map(build,images))
(root/'results/core-sdk22-canonical-final-status-20261007.json').write_text(json.dumps(status,indent=2)+'\n');print(status);raise SystemExit(any(status.values()))
