# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import json,resource,signal,subprocess
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
w=Path('/fixture'); flags=json.loads((w/'obs-compile-flags.json').read_text())
subprocess.run(['g++','--version'],check=True)
for kind in ('original','fixed'):
 r=subprocess.run(['g++',*flags,'-c',str(w/(kind+'.cc')),'-o',str(w/(kind+'.o'))],capture_output=True,text=True)
 (w/(kind+'-compile.log')).write_text(r.stdout+r.stderr)
 if kind=='original':
  assert r.returncode and 'control reaches end of non-void function' in r.stderr,(r.returncode,r.stderr)
  print('Original fails with exact OBS compile flags',flush=True)
 else:
  assert r.returncode==0 and not r.stderr,(r.returncode,r.stderr)
  print('Fixed source compiles with exact OBS compile flags',flush=True)
subprocess.run(['g++',*flags,'-ffunction-sections','-fdata-sections',str(w/'fixed.cc'),'/sources/nodejs24-allocation-status-test.cc','-Wl,--gc-sections','-lnode','-pthread','-o',str(w/'control')],check=True)
subprocess.run([str(w/'control')],check=True)
for index,value in enumerate(['Success','Failed to commit','Ran out of reservation','Hinted address was taken or not found']):
 r=subprocess.run([str(w/'control'),str(index)],capture_output=True,text=True)
 assert r.returncode==0 and r.stdout.strip()==value,(index,r)
for value in ['-1','4','255','256','2147483647','-2147483648']:
 r=subprocess.run([str(w/'control'),value],capture_output=True,text=True)
 assert r.returncode==-signal.SIGABRT and 'unreachable code' in r.stderr,(value,r)
 print('Invalid status rejected:',value,flush=True)
for args in [[''],['4extra'],['2147483648'],['-2147483649'],['0','extra']]:
 r=subprocess.run([str(w/'control'),*args],capture_output=True,text=True)
 assert r.returncode==2 and not r.stderr,(args,r)
subprocess.run(['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','--log-file=/fixture/valgrind.log',str(w/'control')],check=True)
print('All named, invalid, parsing and Valgrind checks passed',flush=True)
