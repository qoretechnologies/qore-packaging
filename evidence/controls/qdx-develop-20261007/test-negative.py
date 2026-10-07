# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,os,re,shutil,subprocess
root=Path.cwd();repo=root.parent/'qore';out=root/'results/qdx-develop-negative-20261007';out.mkdir();stage=out/'source'
shutil.copytree(root/'results/qdx-develop-tests2-20261007/source',stage,symlinks=True)
shutil.copy2(root/'work/qdx-develop-20261007/before/qlib/Qdx.qm',stage/'qlib/Qdx.qm')
env=os.environ.copy();env.pop('LD_PRELOAD',None);env['LD_LIBRARY_PATH']=str(repo/'build');env['QORE_MODULE_DIR_ONLY']='1';env['QORE_INCLUDE_DIR']='';env['QORE_MODULE_DIR']=':'.join([str(stage/'qlib'),*[str(p) for p in sorted((repo/'build/modules').iterdir()) if p.is_dir()],str(repo.parent/'module-xml/build')])
cmd=[str(repo/'build/qore'),'-b','--enable-debug',str(stage/'examples/test/qlib/Qdx/AstProcessor.qtest')]
with (out/'test.log').open('w') as f:r=subprocess.run(cmd,env=env,cwd=repo,stdout=f,stderr=subprocess.STDOUT)
(out/'status.json').write_text(json.dumps({'command':cmd,'exit_code':r.returncode},indent=2)+'\n');print(r.returncode)
assert r.returncode==3
s=(out/'test.log').read_text();assert '29 test cases' in s and '26 succeeded' in s and '3 errors' in s,s
