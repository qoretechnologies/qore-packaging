# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import subprocess,json
out=Path('/control');records=[]
for name,cmd in [
 ('compile',['g++','-std=c++20','-O2','-g','-Wall','-Wextra','-Werror','-DV8_ENABLE_CHECKS','-isystem','/usr/include/node','/control/control.cc','-lnode','-pthread','-o','/control/control']),
 ('ordinary',['/control/control','ordinary']),
 ('shared',['/control/control','shared'])]:
 with (out/(name+'2.log')).open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 records.append(dict(name=name,command=cmd,exit_code=r.returncode));(out/'status2.json').write_text(json.dumps(records,indent=2)+'\n')
 if name=='compile':r.check_returncode()
