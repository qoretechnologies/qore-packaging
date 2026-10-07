# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,shutil,subprocess
root=Path.cwd();repo=root/'work/checkouts/qore-documentation-sdk-20261006';out=root/'results/qdx-literal-fix4-20261007';out.mkdir()
image=json.loads((root/'results/core-doc-render-image-20261007/status.json').read_text())['image']
records=[]
for variant in ['fixed','original']:
 stage=out/variant;qlib=stage/'src/qlib';qlib.mkdir(parents=True)
 for p in (repo/'qlib').iterdir():
  if p.name=='Qdx.qm':continue
  (qlib/p.name).symlink_to('/src/qlib/'+p.name)
 source=repo/'qlib/Qdx.qm' if variant=='fixed' else root/'work/qdx-literal-fix-20261007/before/qlib/Qdx.qm'
 shutil.copy2(source,qlib/'Qdx.qm')
 tests=stage/'src/examples/test/qlib/Qdx';tests.mkdir(parents=True)
 for p in (repo/'examples/test/qlib/Qdx').glob('*.qtest'):shutil.copy2(p,tests/p.name)
 common=['docker','run','--rm','--init','--network','none','--user','1019:100','-e','QORE_MODULE_DIR=/out/src/qlib:/usr/lib64/qore-modules/3.0.0','-e','QORE_MODULE_DIR_ONLY=1','-v',str(repo)+':/src:ro','-v',str(stage)+':/out',image]
 commands=[['qcc','-O3','-m','/out/src/qlib/Qdx.qm','-o','/out/src/qlib/Qdx.qmod'],['qore','-b','--enable-debug','/out/src/examples/test/qlib/Qdx/AstProcessor.qtest']]
 row={'variant':variant,'steps':[]}
 for i,command in enumerate(commands):
  with (stage/f'{i}.log').open('w') as log:r=subprocess.run([*common,*command],stdout=log,stderr=subprocess.STDOUT)
  row['steps'].append({'command':command,'exit_code':r.returncode})
  if r.returncode:break
 records.append(row);(out/'status.json').write_text(json.dumps(records,indent=2)+'\n');print(row,flush=True)
