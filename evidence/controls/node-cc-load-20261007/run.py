# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import subprocess,json
out=Path('/control');records=[]
for mode in ('release','debug'):
 commands=[('compile',['g++','-std=c++20','-O3' if mode=='release' else '-O2','-g','-Wall','-Wextra','-Wmaybe-uninitialized','-Werror=return-type',str(out/'control.cc'),'-o',str(out/mode)]),('normal',[str(out/mode)]),('memory',['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','--log-file='+str(out/(mode+'-valgrind.log')),str(out/mode)])]
 for label,command in commands:
  with (out/(mode+'-'+label+'.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
  records.append(dict(mode=mode,label=label,command=command,exit_code=r.returncode));(out/'status.json').write_text(json.dumps(records,indent=2)+'\n');r.check_returncode()
print('Four control runs complete.')
