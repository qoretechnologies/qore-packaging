# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
out=Path('/work');records=[]
for name,mode in [('original','debug'),('fixed','debug'),('fixed','release')]:
 stem=name+'-'+mode
 commands=[['g++','-std=c++20','-g','-O0' if mode=='debug' else '-O2','-Wall','-Wextra']+(['-DDEBUG'] if mode=='debug' else [])+['/work/'+name+'.cc','-o','/work/'+stem],['/work/'+stem]+(['baseline'] if name=='original' else []),['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/work/'+stem+'-valgrind.log','/work/'+stem]+(['baseline'] if name=='original' else [])]
 for phase,cmd in zip(('compile','normal','memory'),commands):
  with (out/(stem+'-'+phase+'.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  records.append({'name':stem+'-'+phase,'command':cmd,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(records,indent=2)+'\n')
  if not(name=='original' and phase=='memory'):r.check_returncode()
  elif r.returncode!=99:raise AssertionError(('baseline did not expose uninitialized trace',r.returncode))
