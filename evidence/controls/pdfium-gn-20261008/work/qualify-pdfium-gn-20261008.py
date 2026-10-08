# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,subprocess,tarfile,shutil
root=Path.cwd();out=root/'results/pdfium-gn-20261008';out.mkdir(exist_ok=False)
settings={'fedora':'fedora-pdfium-candidate-7','leap':'leap-pdfium-candidate-10','el10':'el10-pdfium-candidate-10'}
info=json.loads((root/'evidence/pdfium-lto-qualification-20261003.json').read_text())
archive=root/'cache/qore-pdfium_148.0.7778+ds.orig.tar.xz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()=='7e3465f432a31696486c8505cbe59a06c85247101651621630fd9adaf033689d'
# Every target gets the exact canonical repack and current three patches.
def qualify(target):
 dest=out/target;dest.mkdir();tree=dest/'source';tree.mkdir()
 with tarfile.open(archive) as tf:tf.extractall(tree,filter='data')
 src=next(tree.iterdir());(src/'rpm').mkdir(exist_ok=True)
 for name in ['pdfium-rpm-shared-library.patch','pdfium-rpm-tests.patch','pdfium-system-freetype-hinting.patch']:
  with (dest/(name+'.log')).open('w') as log:
   subprocess.run(['patch','-p1','-i',str(root/'dependencies'/name)],cwd=src,stdout=log,stderr=subprocess.STDOUT,check=True)
 if target=='el10':
  ft=src/'third_party/freetype/src';ft.mkdir(parents=True,exist_ok=True)
  with tarfile.open(root/'cache/pdfium-freetype-99b479dc.tar.xz') as tf:tf.extractall(ft,filter='data')
 previous=next((root/'results'/settings[target]).glob('rpmbuild/BUILD/**/gn-src/out/gn'))
 # Verify every source file in the reused bootstrap's GN tree against the pinned repack.
 gnroot=previous.parents[1];count=0
 for path in (src/'gn-src').rglob('*'):
  if path.is_file():
   old=gnroot/path.relative_to(src/'gn-src')
   assert path.read_bytes()==old.read_bytes(),str(path)
   count+=1
 (src/'gn-src/out').mkdir();shutil.copy2(previous,src/'gn-src/out/gn')
 shutil.copy2(root/'dependencies/pdfium-rpm-build.py',src/'rpm/build.py')
 (dest/'gn-source.json').write_text(json.dumps({'identical_gn_source_files':count,'reused_binary':str(previous.relative_to(root)),'binary_sha256':hashlib.sha256(previous.read_bytes()).hexdigest()},indent=2)+'\n')
 cmd=['docker','run','--rm','--init','--network','none','--user','1019:100','-v',str(dest)+':/control','-v',str(root/'work/pdfium-gn-control-20261008.py')+':/control.py:ro','-w','/control/source/'+src.name,info['targets'][target]['image'],'python3','/control.py',target]
 (dest/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
 with (dest/'driver.log').open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 print(target,r.returncode,flush=True);return target,r.returncode
with ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(qualify,settings))
(out/'status.json').write_text(json.dumps(results,indent=2)+'\n')
assert not any(results.values()),results
