# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess
root=Path.cwd();repo=root/'work/checkouts/qore-documentation-sdk-20261006';out=root/'results/core-doc-literal-regression2-20261007';out.mkdir()
def run(target):
 image=json.loads((root/f'results/{target}-core-doc-sdk22-candidate4-20261007/build.json').read_text())['image'];cmd=['docker','run','--rm','--network','none','--user','1019:100','-v',str(repo)+':/src:ro',image,'python3','-B','-W','error','/src/examples/test/cmake/test_doc_literal_escaping.py','-v']
 with (out/(target+'.log')).open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 version=subprocess.check_output(['docker','run','--rm','--network','none',image,'doxygen','--version'],text=True).strip()
 return target,{'exit_code':r.returncode,'command':cmd,'doxygen':version}
with ThreadPoolExecutor(max_workers=3) as pool:rows=dict(pool.map(run,['fedora','leap','el10']))
(out/'status.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows);assert all(r['exit_code']==0 for r in rows.values())
