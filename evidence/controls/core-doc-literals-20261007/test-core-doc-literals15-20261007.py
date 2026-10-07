# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,re,subprocess,hashlib
root=Path.cwd();out=root/'results/core-doc-literals15-20261007';out.mkdir();changes=json.loads((root/'work/core-doc-literals10-20261007/changes.json').read_text())
files={'lib/QC_HTTPClient.qpp':'QC_HTTPClient.dox.h','qlib/TableMapper.qm':'doxygen/qlib/TableMapper/TableMapper.qm.dox.h','doxygen/lang/900_release_notes.dox.tmpl':'900_release_notes.dox'}
modules=['ConnectionProvider','ServerSentEventClient','SewioWebSocketClient','TableMapper','WebSocketClient']
def run(target):
 base=root/f'results/{target}-core-doc-sdk22-candidate4-20261007';builds=list((base/'rpmbuild/BUILD').glob('*/build'))+list((base/'rpmbuild/BUILD').glob('*/*/build'));assert len(builds)==1,builds;build=builds[0];inside='/work/'+str(build.relative_to(base));image=json.loads((base/'build.json').read_text())['image'];dest=out/target;dest.mkdir();rows=[]
 for variant in ['original','fixed']:
  v=dest/variant;v.mkdir()
  for row in changes:
   name=files[row['file']];s=(build/name).read_text()
   for a,b in row['changes']:
    assert s.count(a)==1,(target,name,a,s.count(a))
    if variant=='fixed':s=s.replace(a,b)
   (v/Path(name).name).write_text(s)
  phases=['lang-index']+(['lang-render',*modules] if variant=='fixed' else ['TableMapper'])
  for phase in phases:
   path=build/'doxygen'/('Doxyfile.lang.final' if phase.startswith('lang') else 'Doxyfile.'+phase)
   if not phase.startswith('lang') and Path(str(path)+'.final').exists():path=Path(str(path)+'.final')
   cfg=path.read_text()
   if path.name.endswith('.final') and not phase.startswith('lang'):
    inherited=(build/'doxygen'/('Doxyfile.'+phase)).read_text()
    cfg=inherited+'\n'+re.sub(r'^@INCLUDE = .*$', '', cfg, flags=re.M)
   assert not re.search(r'^@INCLUDE\s*=',cfg,re.M),path
   for rel in files.values():
    cfg=cfg.replace(inside+'/'+rel,'/out/'+variant+'/'+Path(rel).name)
    if '/' not in rel:cfg=re.sub(r'(?<![\w/])'+re.escape(rel)+r'(?![\w])','/out/'+variant+'/'+rel,cfg)
   if variant=='fixed' and phase not in ['lang-index','lang-render']:
    cfg=cfg.replace(inside+'/qore.tag=','/out/fixed/qore.tag=')
    cfg=re.sub(r'(?<![\w/])qore\.tag=',r'/out/fixed/qore.tag=',cfg)
   cfg+='\nOUTPUT_DIRECTORY = /out/'+variant+'/'+phase+'\nWARN_IF_DOC_ERROR = YES\n'
   cfg+='GENERATE_TAGFILE = '+('/out/'+variant+'/qore.tag' if phase=='lang-index' else '')+'\n'
   if phase=='lang-index':cfg+='GENERATE_HTML = NO\n'
   p=v/('Doxyfile.'+phase);p.write_text(cfg)
   cmd=['docker','run','--rm','--init','--network','none','--user','1019:100','-v',str(base)+':/work:ro','-v',str(dest)+':/out','-w',inside,image,'doxygen','/out/'+variant+'/'+p.name]
   log=v/(phase+'.log')
   with log.open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
   warnings=[s for s in log.read_text().splitlines() if re.search(r'(?i)warning:|error:',s)]
   rows.append({'variant':variant,'phase':phase,'exit_code':r.returncode,'diagnostics':warnings,'command':cmd});(dest/'status.json').write_text(json.dumps(rows,indent=2)+'\n');print(target,variant,phase,r.returncode,len(warnings),flush=True)
   assert r.returncode==0,(target,phase,log.read_text()[-2000:])
   if variant=='fixed':assert not warnings,(target,phase,warnings)
 return target,rows
with ThreadPoolExecutor(max_workers=3) as pool:record=dict(pool.map(run,['fedora','leap','el10']))
(out/'status.json').write_text(json.dumps(record,indent=2)+'\n')
