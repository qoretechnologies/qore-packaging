# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
out=Path('/control');root=Path('/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1');records=[]
commands=[('helper',['python3','/dependencies/nodejs24-reschedule-test.py','--source',str(root),'--test-source','/dependencies/nodejs24-reschedule-test.cc','--output','/control/reschedule']),('memory',['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/control/valgrind.log','/control/reschedule'])]
for name,cmd in commands:
 with (out/(name+'.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 records.append(dict(name=name,command=cmd,exit_code=r.returncode));(out/'status.json').write_text(json.dumps(records,indent=2)+'\n');r.check_returncode()
