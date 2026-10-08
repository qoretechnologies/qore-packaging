# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess,json
out=Path('results/pdfium-gn-20261008')
def run(target):
 d=out/target;cmd=json.loads((d/'command.json').read_text())
 with (d/'final-driver.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 print(target,p.returncode,flush=True);return target,p.returncode
with ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(run,['fedora','leap','el10']))
(out/'final-status.json').write_text(json.dumps(results,indent=2)+'\n')
assert not any(results.values()),results
