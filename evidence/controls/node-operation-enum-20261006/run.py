# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
out=Path('/work');results=[]
for mode in ('release','debug'):
 commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra']+(['-DDEBUG'] if mode=='debug' else [])+['/work/control.cc','-o','/work/control-'+mode],['/work/control-'+mode],['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/work/'+mode+'-valgrind.log','/work/control-'+mode]]
 for name,command in zip(('compile','normal','memory'),commands):
  with (out/(mode+'-'+name+'.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
  results.append({'name':mode+'-'+name,'command':command,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(results,indent=2)+'\n');r.check_returncode()
