# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,shlex,subprocess
out=Path('/work');results=[]
flags=['-I/source/deps/v8/include', '-Wno-unused-parameter']
for mode in ('release','debug'):
 commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra']+(['-DDEBUG'] if mode=='debug' else [])+['/work/control.cc',*flags,'-o','/work/control-'+mode],['/work/control-'+mode],['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/work/'+mode+'-valgrind2.log','/work/control-'+mode]]
 for name,command in zip(('compile','normal','memory'),commands):
  with (out/(mode+'-'+name+'2.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
  results.append({'name':mode+'-'+name,'command':command,'exit_code':r.returncode});(out/'status2.json').write_text(json.dumps(results,indent=2)+'\n');r.check_returncode()
