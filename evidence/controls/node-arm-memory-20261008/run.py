# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
root=Path('/control');records=[]
for compress,sandbox in [(False,False),(True,False),(True,True)]:
 for mode in ['release','debug']:
  stem=mode+'-c'+str(int(compress))+'-s'+str(int(sandbox))
  flags=['-DV8_COMPRESS_POINTERS'] if compress else []
  flags+=['-DDEBUG'] if mode=='debug' else ['-DNDEBUG']
  commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra','-Wswitch-enum','-Werror=switch-enum','-DSANDBOX='+str(int(sandbox)),*flags,'/control/control.cc','-o','/control/'+stem],['/control/'+stem],['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','/control/'+stem]]
  for step,cmd in zip(['compile','normal','valgrind'],commands):
   with (root/(stem+'-'+step+'.log')).open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
   records.append({'name':stem+'-'+step,'command':cmd,'exit_code':r.returncode})
   (root/'status.json').write_text(json.dumps(records,indent=2)+'\n')
   r.check_returncode()
