# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
p=Path('/fixture')
commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra','-Wmaybe-uninitialized','-I/source/deps/v8','/fixture/control.cc','-o','/fixture/control'],['/fixture/control'],['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','--log-file=/fixture/valgrind.log','/fixture/control']]
results=[]
for name,command in zip(('compile','normal','memory'),commands):
 with (p/(name+'.log')).open('w') as stream:r=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
 results.append({'name':name,'command':command,'exit_code':r.returncode});(p/'status.json').write_text(json.dumps(results,indent=2)+'\n');r.check_returncode()
