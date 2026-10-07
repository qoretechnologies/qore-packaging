# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,shlex,signal,subprocess
out=Path('/work');flags=shlex.split(subprocess.check_output(['pkg-config','--cflags','--libs','icu-i18n','icu-uc'],text=True));records=[]
def run(name,command,expected=0):
 with (out/(name+'.log')).open('x') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 records.append(dict(name=name,exit_code=r.returncode,expected=expected,command=command));(out/'status.json').write_text(json.dumps(records,indent=2)+'\n');assert r.returncode==expected,(name,r.returncode,expected)
for mode in ('release','debug'):
 binary='/work/fixed-'+mode
 run(mode+'-compile',['g++','-std=c++20','-g','-Wall','-Wextra','-Werror',*(['-O2','-DNDEBUG'] if mode=='release' else ['-O0','-DDEBUG']),'/work/fixed.cc',*flags,'-o',binary])
 run(mode+'-normal',[binary]);run(mode+'-memory',['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/work/'+mode+'-valid-valgrind.log',binary])
 for index in ('-1','-2','-2147483648','638','2147483647'):
  label=mode+'-invalid-'+index
  run(label,[binary,index],-signal.SIGABRT)
  run(label+'-memory',['valgrind','--error-exitcode=99','--leak-check=no','--log-file=/work/'+label+'-valgrind.log',binary,index],-signal.SIGABRT)
  assert 'ERROR SUMMARY: 0 errors' in (out/(label+'-valgrind.log')).read_text()
  expected='(index) > (0)' if index.startswith('-') else 'id != nullptr'
  assert 'CHECK failed: '+expected in (out/(label+'.log')).read_text()
