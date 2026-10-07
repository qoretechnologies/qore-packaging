# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
out=Path('/control');records=[]
commands=[('versions',['rpm','-qa','*cares*']),('compile',['gcc','-std=c11','-O2','-g','-Wall','-Wextra','-Werror','/control/control.c','-lcares','-o','/control/control']),('normal',['/control/control']),('memory',['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/control/native-valgrind2.log','/control/control'])]
for name,cmd in commands:
 with (out/('native-'+name+'2.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 records.append(dict(name=name,command=cmd,exit_code=r.returncode));(out/'native-status2.json').write_text(json.dumps(records,indent=2)+'\n');r.check_returncode()
