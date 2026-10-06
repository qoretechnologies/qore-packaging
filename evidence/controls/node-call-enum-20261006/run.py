# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
out=Path('/work');results=[]
for wasm in (0,1):
 for mode in ('release','debug'):
  stem=f'{mode}-wasm{wasm}'
  commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra',f'-DV8_ENABLE_WEBASSEMBLY={wasm}']+(['-DDEBUG'] if mode=='debug' else [])+['/work/control.cc','-o','/work/control-'+stem],['/work/control-'+stem],['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/work/'+stem+'-valgrind.log','/work/control-'+stem]]
  for name,command in zip(('compile','normal','memory'),commands):
   with (out/(stem+'-'+name+'.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
   results.append({'name':stem+'-'+name,'command':command,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(results,indent=2)+'\n');r.check_returncode()
