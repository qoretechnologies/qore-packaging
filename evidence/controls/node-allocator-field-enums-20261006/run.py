# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import subprocess,json
w=Path('/work');results=[]
commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra','/work/control.cc','-o','/work/control'],['/work/control'],['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/work/valgrind.log','/work/control']]
for name,command in zip(('compile','normal','memory'),commands):
 with (w/(name+'.log')).open('w') as f:r=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT)
 results.append({'name':name,'command':command,'exit_code':r.returncode});(w/'status.json').write_text(json.dumps(results,indent=2)+'\n');r.check_returncode()
