# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import subprocess,sys,os,json,hashlib
root=Path.cwd();mode=sys.argv[1];assert mode in ('release','debug');source=root/'work/checkouts/qore-aot-runtime-dependencies-20261008';build=source/('build' if mode=='release' else 'build-debug');out=root/f'results/aot-runtime-origin-{mode}-checks-20261008';out.mkdir()
assert json.loads((root/f'results/aot-runtime-origin-build-20261008/{mode}-status.json').read_text())['exit_code']==0
env=dict(os.environ,LD_LIBRARY_PATH=str(build),QORE_LIBDIR=str(build),QORE_BIN=str(build/'qore'),QORE_TEST_QORE=str(build/'qore'),QORE_TEST_QCC=str(build/'qcc'),QORE_MODULE_DIR=str(source/'qlib'))
steps=[('qcc-rpm',['python3','-B','-W','error',str(source/'rpm/tests/qcc-rpm-integration.py'),'-v'])]
for name in ['AOTModuleContextPath','IRScalarCSE','IRScalarCSETemporaryLifetime']:
 steps.append((name,[str(build/'qore'),'-b','--enable-debug',str(source/f'examples/test/ir/{name}.qtest')]))
steps.append(('identity-valgrind',['python3',str(root/'work/qualify-aot-runtime-origin-identity-20261008.py'),mode]))
records=[]
for name,args in steps:
 print(mode,name,flush=True)
 with (out/(name+'.log')).open('w') as log:r=subprocess.run(args,env=env,stdout=log,stderr=subprocess.STDOUT)
 records.append({'name':name,'command':args,'exit_code':r.returncode});(out/'steps.json').write_text(json.dumps(records,indent=2)+'\n');assert r.returncode==0,(mode,name,r.returncode)
(out/'status.json').write_text(json.dumps({'mode':mode,'exit_code':0,'steps':len(records),'library_sha256':hashlib.sha256((build/'libqore.so.20.0.0').read_bytes()).hexdigest()},indent=2)+'\n');print(mode,'all final checks passed',flush=True)
