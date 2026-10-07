# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import json,resource,signal,subprocess
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CORE,(0,0));w=Path('/fixture')
flags=subprocess.check_output(['rpm','--eval','%{optflags}'],text=True).split()
common=['g++',*flags,'-std=c++20','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-Wall','-Werror','-I/v8','-I/v8/include','-I/v8/third_party/abseil-cpp']
r=subprocess.run([*common,'/sources/nodejs24-torque-stack-test.cc','-lnode','-pthread','-o','/fixture/control'],capture_output=True,text=True)
(w/'fixed-compile.log').write_text(r.stdout+r.stderr)
assert r.returncode==0 and not r.stderr,(r.returncode,r.stderr)
subprocess.run(['/fixture/control'],check=True)
for value in ['5','255','4294967295','18446744073709551615']:
 r=subprocess.run(['/fixture/control',value],capture_output=True,text=True)
 assert r.returncode==-signal.SIGABRT and 'elements_.size() >= count' in r.stderr,(value,r)
 print('Invalid Torque kind rejected:',value,flush=True)
for args in [[''],['4extra'],['18446744073709551616'],['-1'],['0','extra']]:
 r=subprocess.run(['/fixture/control',*args],capture_output=True,text=True)
 assert r.returncode==2 and not r.stderr,(args,r)
subprocess.run(['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=definite,indirect,possible','--log-file=/fixture/valgrind.log','/fixture/control'],check=True)
print('Torque stack control passes',flush=True)
