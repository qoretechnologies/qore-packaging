# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
out=Path('/work');results=[]
for tagged in (4,8):
 for mode in ('release','debug'):
  name=mode+'-'+str(tagged)
  commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra','-Wno-unused-parameter','-DTEST_TAGGED_SIZE='+str(tagged)]+(['-DDEBUG'] if mode=='debug' else [])+['/work/control.cc','/work/helper.cc','-o','/work/control-'+name],['/work/control-'+name],['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/work/'+name+'-valgrind.log','/work/control-'+name]]
  for phase,command in zip(('compile','normal','memory'),commands):
   with (out/(name+'-'+phase+'.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
   results.append(dict(name=name+'-'+phase,command=command,exit_code=r.returncode));(out/'status.json').write_text(json.dumps(results,indent=2)+'\n');r.check_returncode()
