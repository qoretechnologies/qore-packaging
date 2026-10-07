# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,re,shutil,subprocess,os,select
# Join the one image-preparation process before consuming its result.
fds=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  argv=(proc/'cmdline').read_bytes().decode().split('\0')
  if 'work/prepare-core-doc-render-image-20261007.py' in argv:fds.append(os.pidfd_open(int(proc.name)))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
assert len(fds)<=1
if fds:
 print('Joining installed SDK image preparation.',flush=True);select.select(fds,[],[]);os.close(fds[0])
root=Path.cwd();repo=root/'work/checkouts/qore-documentation-sdk-20261006';sdk=root/'work/core-sdk22-render-inputs-20261007';out=root/'results/core-doc-corrections-render9-20261007';out.mkdir();(out/'configs').mkdir();(out/'logs').mkdir()
image=json.loads((root/'results/core-doc-render-image-20261007/status.json').read_text())['image']
for p in sdk.glob('*.tag'):shutil.copy2(p,out/p.name)
rows=json.loads((root/'work/core-doc-final-qlib-diagnostics-20261007.json').read_text())
# Inventory is the complete finished candidate3 Doxygen pass.
mods=sorted({(r if isinstance(r,str) else r['file']).split('/')[0] for r in rows})
mods = sorted(set(mods) | {"ImapClientDataProvider", "RestClientDataProvider", "SGLangRestClient"})
assert len(mods)>70,mods
extra={m:peers.split() for m,peers in re.findall(r'^set\(QORE_DOC_EXTRA_MODULES_(\w+) ([^\n]*)\)$',(repo/'CMakeLists.txt').read_text(),re.M)}
for mod in mods:
 (out/'doxygen/qlib'/mod).mkdir(parents=True)
 (out/'docs/modules'/mod).mkdir(parents=True)
 s=(sdk/'doxygen'/('Doxyfile.'+mod)).read_text()
 s=re.sub(r'/work/rpmbuild/BUILD/[^\s"=]*/build/doxygen/qlib/','/out/doxygen/qlib/',s)
 s=re.sub(r'/work/rpmbuild/BUILD/[^\s"=]*/build/modules/','/sdk/modules/',s)
 s=re.sub(r'(?<!\S)\.\./doxygen/', '/src/doxygen/',s).replace('/work/rpmbuild/BUILD/qore-3.0.0~git20261006.22','/src')
 for peer in extra.get(mod,[]):
  tag='/sdk/modules/'+peer+'/'+peer+'.tag' if (sdk/'modules'/peer/(peer+'.tag')).exists() else peer+'.tag'
  assert (sdk/'modules'/peer/(peer+'.tag')).exists() or (out/(peer+'.tag')).exists(),(mod,peer)
  if peer+'.tag=' not in s:s+='\nTAGFILES += "'+tag+'=../../'+peer+'/html"\n'
 for phase in ['index','render']:
  cfg=s+'\nWARN_IF_DOC_ERROR = '+('NO' if phase=='index' else 'YES')+'\n'
  if phase=='index':
   # Read immutable seed indexes while generating replacements in parallel.
   cfg=re.sub(r'(?<![/\w])([A-Za-z0-9_]+\.tag)=',r'/sdk/\1=',cfg)
   cfg+='GENERATE_HTML = NO\n'
  else:cfg=re.sub(r'^GENERATE_TAGFILE\s*=.*$', 'GENERATE_TAGFILE =',cfg,flags=re.M)
  (out/'configs'/('Doxyfile.'+mod+'.'+phase)).write_text(cfg)
common=['docker','run','--rm','--init','--network','none','--user','1019:100','-e','QORE_MODULE_DIR=/src/qlib:/usr/lib64/qore-modules/3.0.0','-e','QORE_MODULE_DIR_ONLY=1','-e','QORE_DOC_DEFINES=QORE_QDX_RUN,Unix,HAVE_TERMIOS','-v',str(repo)+':/src:ro','-v',str(sdk)+':/sdk:ro','-v',str(out)+':/out','-w','/out',image]
def run(mod,phase):
 src='/src/qlib/'+(mod if (repo/'qlib'/mod).is_dir() else mod+'.qm')
 body='set -eu\n'
 if phase=='index':body+='qore -b --enable-debug /src/doxygen/qdx --strict-tables "$1" "/out/doxygen/qlib/$2/$2.qm.dox.h"\n'
 body+='doxygen "/out/configs/Doxyfile.$2.$3"\n'
 if phase=='render':body+='qore -b --enable-debug /src/doxygen/qdx --post "/out/docs/modules/$2/html" "/out/docs/modules/$2/html/search"\n'
 with (out/'logs'/(mod+'.'+phase+'.log')).open('w') as log:r=subprocess.run([*common,'sh','-c',body,'render',src,mod,phase],stdout=log,stderr=subprocess.STDOUT)
 return mod,r.returncode
record={'modules':mods,'image':image}
probe=run(mods[0],'index');assert probe[1]==0,(probe,(out/'logs'/(mods[0]+'.index.log')).read_text())
for phase in ['index','render']:
 with ThreadPoolExecutor(max_workers=3) as pool:record[phase]=dict(pool.map(lambda mod:run(mod,phase),mods))
 (out/'status.json').write_text(json.dumps(record,indent=2)+'\n')
 print(phase,dict(__import__('collections').Counter(record[phase].values())),flush=True)
 if any(record[phase].values()):raise SystemExit(1)
