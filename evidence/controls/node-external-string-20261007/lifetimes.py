# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import subprocess,json,signal
out=Path('/control');records=[]
link=['g++','-std=c++20','-O2','-g','-Wall','-Wextra','-Werror','-isystem','/usr/include/node','/control/regression7.cc','/control/fixed-adapter.o','-lnode','-licuuc','-lcrypto','-pthread','-Wl,--export-dynamic-symbol=_ZNK2v86String28VerifyExternalStringResourceEPNS0_22ExternalStringResourceE','-o','/control/regression7']
commands=[('regression7-compile',link,0)]
for mode in ('ordinary','shared'):
 for count in ('0','1','100','1000'):
  name=mode+'-lifetimes-'+count
  commands += [(name,['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','--log-file=/control/'+name+'-valgrind.log','/control/regression7',mode,count],0)]
for name,cmd,expected in commands:
 with (out/(name+'.log')).open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 records.append(dict(name=name,command=cmd,exit_code=r.returncode,expected=expected));(out/'lifetimes-status.json').write_text(json.dumps(records,indent=2)+'\n')
 if name=='regression7-compile':r.check_returncode()
