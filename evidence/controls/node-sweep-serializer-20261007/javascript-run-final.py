# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
root=Path.cwd();out=root/'work/node-sweep-serializer-controls-20261007';records=[]
for pgo in (True,False):
 for minor_ms in (False,True):
  name=f'javascript-pgo{int(pgo)}-minor{int(minor_ms)}'
  cmd=['docker','run','--rm','--network','none','--user','1019:100','-v',str(out)+':/work:ro','qore-rpm-keep:leap-node-compaction-baseline2-20261006','node','--expose-gc','--profile-guided-optimization' if pgo else '--no-profile-guided-optimization']
  if minor_ms:cmd.append('--minor-ms')
  cmd.append('/work/control.js')
  with (out/(name+'-final.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  records.append(dict(name=name,command=cmd,exit_code=r.returncode));(out/'javascript-status-final.json').write_text(json.dumps(records,indent=2)+'\n');r.check_returncode()
