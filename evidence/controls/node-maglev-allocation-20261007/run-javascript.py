# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json, subprocess
out = Path('work/node-maglev-allocation-controls-20261007')
records = []
for level in range(3):
    command = ['docker','run','--rm','--network','none','--user','1019:100',
               '-v',str(out.resolve())+':/work:ro',
               'qore-rpm-keep:leap-node-compaction-baseline2-20261006',
               'node','--maglev','--no-turbofan','--allow-natives-syntax',
               '--no-concurrent-recompilation','--expose-gc',
               '--maglev-allocation-folding='+str(level),'/work/control.js']
    with (out/f'javascript-{level}.log').open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    records.append(dict(folding_level=level, command=command, exit_code=result.returncode))
    (out/'javascript-status.json').write_text(json.dumps(records,indent=2)+'\n')
    result.check_returncode()
