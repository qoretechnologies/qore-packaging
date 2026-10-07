# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,os,re,select,shutil,subprocess
root=Path.cwd();repo=root.parent/'qore';out=root/'results/qdx-develop-tests2-20261007';out.mkdir()
fds=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  argv=(proc/'cmdline').read_bytes().decode().split('\0')
  if argv[1:6]==['--build','build','--target','Qdx-qmod','-j2'] and Path(argv[0]).name=='cmake':fds.append(os.pidfd_open(int(proc.name)))
 except (FileNotFoundError,ProcessLookupError,PermissionError):pass
assert len(fds)<=1
if fds:select.select(fds,[],[]);os.close(fds[0])
log=(root/'results/qdx-develop-qmod-build-20261007.log').read_text();assert 'Built target Qdx-qmod' in log,log[-2000:]
qmod=repo/'qlib/Qdx.qmod';assert qmod.stat().st_mtime>(repo/'qlib/Qdx.qm').stat().st_mtime
stage=out/'source';(stage/'qlib').mkdir(parents=True)
for p in (repo/'qlib').iterdir():
 if p.name in ['Qdx.qm','Qdx.qmod']:continue
 (stage/'qlib'/p.name).symlink_to(p)
shutil.copy2(repo/'qlib/Qdx.qm',stage/'qlib/Qdx.qm')
(stage/'build').symlink_to(repo/'build',target_is_directory=True)
tests=stage/'examples/test/qlib/Qdx';tests.mkdir(parents=True)
for p in (repo/'examples/test/qlib/Qdx').glob('*.qtest'):shutil.copy2(p,tests/p.name)
env=os.environ.copy();env.pop('LD_PRELOAD',None);env['LD_LIBRARY_PATH']=str(repo/'build');env['QORE_MODULE_DIR_ONLY']='1'
paths=[str(p) for p in sorted((repo/'build/modules').iterdir()) if p.is_dir()] + [str(repo.parent/'module-xml/build')]
rows=[]
for mode,tree in [('aot',repo),('source',stage)]:
 env['QORE_MODULE_DIR']=':'.join([str(tree/'qlib'),*paths]);env['QORE_INCLUDE_DIR']=''
 for test in sorted((tree/'examples/test/qlib/Qdx').glob('*.qtest')):
  cmd=[str(repo/'build/qore'),'-b','--enable-debug',str(test)]
  with (out/(mode+'-'+test.stem+'.log')).open('w') as f:r=subprocess.run(cmd,env=env,cwd=repo,stdout=f,stderr=subprocess.STDOUT)
  rows.append({'mode':mode,'test':test.name,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows[-1],flush=True)
  assert r.returncode==0
for p in out.glob('*.log'):
 s=p.read_text();assert not re.search(r'(?i)warning|skipped|exception',s),(p,s)
assert len(rows)==6
