# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess
root=Path.cwd();old=json.loads((root/'results/ignored-qpp-spec-20261008/status.json').read_text());out=root/'results/operator-effects-spec-20261008';out.mkdir()
def run(target):
 cmd=[s.replace('qore-ignored-qpp-20261008','qore-operator-effects-20261008') for s in old[target]['command']]
 with (out/(target+'.log')).open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 print(target,p.returncode,flush=True);return target,{'exit_code':p.returncode,'command':cmd}
with ThreadPoolExecutor(max_workers=3) as pool:r=dict(pool.map(run,old))
(out/'status.json').write_text(json.dumps(r,indent=2)+'\n');assert all(x['exit_code']==0 for x in r.values())
