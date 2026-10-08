# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import os
import subprocess
import sys
root=Path.cwd(); repo=root.parent/'qore'
mode=sys.argv[1]
build=repo/('build-debug' if mode=='debug' else 'build')
out=root/'results/core-separated-path-final-20261008'/mode
out.mkdir(parents=True)
cache=(build/'CMakeCache.txt').read_text()
assert 'CMAKE_INSTALL_PREFIX:PATH=/usr\n' in cache
assert 'CMAKE_BUILD_TYPE:STRING='+('Debug' if mode=='debug' else 'Release')+'\n' in cache
env=os.environ.copy(); env['LD_LIBRARY_PATH']=str(build)
env['QORE_MODULE_DIR']=':'.join([str(repo/'qlib'), *[str(p) for p in (build/'modules').iterdir() if p.is_dir()]])
suites=['examples/test/qore/misc/module-loader/separated-module-path.qtest','examples/test/qore/misc/module-loader/separated-module-shadow.qtest','examples/test/qore/misc/module-loader/modules.qtest','examples/test/qore/parser/module-path-directive.qtest']
records=[]
for suite in suites:
 for vg in [False,True]:
  command=[str(build/'qore'),'-b','--enable-debug',suite,'-v']
  if vg: command=['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=definite,indirect,possible']+command
  name=Path(suite).stem+('-valgrind' if vg else '')
  with (out/(name+'.log')).open('w') as log:
   rc=subprocess.run(command,cwd=repo,env=dict(env, QORE_PCRE2_NO_JIT='1') if vg else env,stdout=log,stderr=subprocess.STDOUT).returncode
  records.append({'name':name,'command':command,'exit_code':rc, 'regex_engine': 'interpreter' if vg else 'default JIT'})
  (out/'status.json').write_text(json.dumps(records,indent=2)+'\n')
  print(mode,name,rc,flush=True)
  if rc: raise SystemExit(rc)
