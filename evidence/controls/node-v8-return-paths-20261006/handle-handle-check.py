# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import resource,signal,subprocess
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
for value in ['-1','2','255','256','2147483647','-2147483648']:
 r=subprocess.run(['/fixture/handle-control',value],capture_output=True,text=True)
 assert r.returncode==-signal.SIGABRT and 'unreachable code' in r.stderr,(value,r)
 print('Invalid handle kind rejected:',value,flush=True)
for args in [[''],['4extra'],['2147483648'],['-2147483649'],['0','extra']]:
 r=subprocess.run(['/fixture/handle-control',*args],capture_output=True,text=True)
 assert r.returncode==2 and not r.stderr,(args,r)
subprocess.run(['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=definite,indirect,possible','--log-file=/fixture/handle-valgrind.log','/fixture/handle-control'],check=True)
print('Handle control passes',flush=True)
