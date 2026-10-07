# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import subprocess,json,signal
out=Path('/control');records=[]
link=['g++','-std=c++20','-O2','-g','-Wall','-Wextra','-Werror','-isystem','/usr/include/node','/control/regression3.cc','/control/fixed-adapter.o','-lnode','-pthread','-Wl,--export-dynamic-symbol=_ZNK2v86String28VerifyExternalStringResourceEPNS0_22ExternalStringResourceE','-o','/control/regression3']
commands=[('regression-compile',link,0)]
for mode in ('ordinary','shared'):
 commands += [(mode+'-regression',['/control/regression3',mode],0),(mode+'-regression-memory',['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','--log-file=/control/'+mode+'-regression3-valgrind.log','/control/regression3',mode],0),(mode+'-negative',['/control/regression3',mode,'negative'],-signal.SIGTRAP)]
for name,cmd,expected in commands:
 with (out/(name+'3.log')).open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 records.append(dict(name=name,command=cmd,exit_code=r.returncode,expected=expected));(out/'regression-status3.json').write_text(json.dumps(records,indent=2)+'\n')
 if name=='regression-compile':r.check_returncode()
