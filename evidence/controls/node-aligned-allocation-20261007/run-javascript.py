# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json, subprocess
out=Path('work/node-aligned-allocation-controls-20261007');records=[]
for name,flags in [('semispace',[]),('slow-stress',['--no-inline-new','--stress-marking=50']),('paged',['--minor-ms','--no-inline-new'])]:
    command=['docker','run','--rm','--network','none','--user','1019:100','-v',str(out.resolve())+':/work:ro','qore-rpm-keep:leap-node-compaction-baseline2-20261006','node','--expose-gc','--max-semi-space-size=1',*flags,'/work/control.js']
    with (out/f'javascript-{name}.log').open('w') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    records.append(dict(name=name,command=command,exit_code=result.returncode))
    (out/'javascript-status.json').write_text(json.dumps(records,indent=2)+'\n')
    result.check_returncode()
