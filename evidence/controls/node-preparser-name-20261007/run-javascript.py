# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
out=Path('work/node-preparser-name-controls-20261007');records=[]
for mode in ('lazy','no-lazy'):
    cmd=['docker','run','--rm','--network','none','--user','1019:100','-v',str(out.resolve())+':/work:ro','qore-rpm-keep:leap-node-compaction-baseline2-20261006','node','--'+mode,'/work/control.js']
    with (out/f'javascript-{mode}.log').open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
    records.append(dict(mode=mode,command=cmd,exit_code=r.returncode));(out/'javascript-status.json').write_text(json.dumps(records,indent=2)+'\n');r.check_returncode()
