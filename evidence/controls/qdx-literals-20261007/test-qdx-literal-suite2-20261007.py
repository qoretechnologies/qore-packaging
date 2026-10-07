# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
root=Path.cwd();repo=root/'work/checkouts/qore-documentation-sdk-20261006';stage=root/'results/qdx-literal-fix4-20261007/fixed';out=root/'results/qdx-literal-suite2-20261007';out.mkdir()
image=json.loads((root/'results/core-doc-render-image-20261007/status.json').read_text())['image']
common=['docker','run','--rm','--init','--network','none','--user','1019:100','-e','QORE_MODULE_DIR=/out/src/qlib:/usr/lib64/qore-modules/3.0.0','-e','QORE_MODULE_DIR_ONLY=1','-v',str(repo)+':/src:ro','-v',str(stage)+':/out:ro',image]
qmod=stage/'src/qlib/Qdx.qmod';saved=qmod.with_suffix('.qmod.saved');rows=[]
try:
 for mode in ['aot','source']:
  if mode=='source':qmod.rename(saved)
  for test in sorted((stage/'src/examples/test/qlib/Qdx').glob('*.qtest')):
   cmd=[*common,'qore','-b','--enable-debug','/out/src/examples/test/qlib/Qdx/'+test.name]
   with (out/(mode+'-'+test.stem+'.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
   rows.append({'mode':mode,'test':test.name,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows[-1],flush=True)
finally:
 if saved.exists():saved.rename(qmod)
assert all(r['exit_code']==0 for r in rows)
