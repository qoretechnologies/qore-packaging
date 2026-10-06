# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import subprocess,json
w=Path('/fixture');flags=json.loads((w/'flags.json').read_text());commands=[[*flags,'-fsyntax-only','/fixture/arity.cc'],['g++','-std=c++20','-O2','-g','-Wall','-Wextra','-I/source/deps/v8','-I/source/deps/v8/include','/fixture/control.cc','-o','/fixture/control'],['/fixture/control'],['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/fixture/valgrind.log','/fixture/control']];results=[]
for name,command in zip(('arity','compile','normal','memory'),commands):
 with (w/(name+'.log')).open('w') as stream:r=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
 results.append({'name':name,'command':command,'exit_code':r.returncode});(w/'status.json').write_text(json.dumps(results,indent=2)+'\n');r.check_returncode()
