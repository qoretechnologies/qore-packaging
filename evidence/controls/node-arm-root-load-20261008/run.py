# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
out=Path('/control');records=[]
for mode in ['release','debug']:
 flags=['-DNDEBUG'] if mode=='release' else ['-DDEBUG']
 commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra',*flags,'/control/control.cc','-o','/control/'+mode],['/control/'+mode],['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','/control/'+mode]]
 for name,command in zip(['compile','normal','valgrind'],commands):
  with (out/(mode+'-'+name+'.log')).open('x') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
  records.append({'name':mode+'-'+name,'command':command,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(records,indent=2)+'\n');r.check_returncode()
