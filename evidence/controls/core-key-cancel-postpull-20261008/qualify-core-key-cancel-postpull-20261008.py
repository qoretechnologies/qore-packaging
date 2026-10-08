# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib,json,os,subprocess
root=Path('/home/david/src/qore/git/qore-packaging');repo=root.parent/'qore'
out=root/'results/core-key-cancel-postpull-20261008';out.mkdir()
paths=['CMakeLists.txt','include/qore/intern/QoreHashKeyHelper.h','examples/test/qore/misc/hash_key_cancel.cpp','examples/test/qore/misc/hash-key-cancel.qtest','design/cooperative-cancellation.md','doxygen/lang/900_release_notes.dox.tmpl']
pins={n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in paths}
(out/'source.json').write_text(json.dumps({'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'files_sha256':pins},indent=2)+'\n')
def qualify(mode):
 build=repo/('build-debug' if mode=='Debug' else 'build');directory=out/mode.lower();directory.mkdir();steps=[]
 cache=(build/'CMakeCache.txt').read_text();assert 'CMAKE_INSTALL_PREFIX:PATH=/usr\n' in cache and 'CMAKE_BUILD_TYPE:STRING='+mode+'\n' in cache
 env={**os.environ,'LD_LIBRARY_PATH':str(build),'QORE_BINARY':str(build/'qore'),'QORE_BIN':str(build/'qore'),'QORE_LIBDIR':str(build)}
 env['QORE_MODULE_DIR']=':'.join([str(build/'qlib-qmod'),str(repo/'qlib'),*[str(p) for p in (build/'modules').iterdir() if p.is_dir()],str(root.parent/'module-xml/build')])
 def run(name,command):
  with (directory/(name+'.log')).open('x') as log:r=subprocess.run(command,cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
  steps.append({'name':name,'command':command,'exit_code':r.returncode});(directory/'steps.json').write_text(json.dumps(steps,indent=2)+'\n');print(mode,name,r.returncode,flush=True);r.check_returncode()
 run('configure',['cmake','-S',str(repo),'-B',str(build),'-DCMAKE_BUILD_TYPE='+mode,'-DCMAKE_INSTALL_PREFIX=/usr'])
 run('build',['cmake','--build',str(build),'--target','qore','qore-hash-key-cancel-test','qore-hash-lookup-test','-j2'])
 for name in ['qore-hash-key-cancel-test','qore-hash-lookup-test']:
  run(name,[str(build/name)])
  run(name+'-valgrind',['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=definite,indirect,possible',str(build/name)])
 for suite in ['misc/hash-key-cancel.qtest','misc/hash-lookup-native.qtest','misc/hash.qtest','misc/hashdecl.qtest','misc/hash-key-encoding/hash-key-encoding.qtest']:
  run(Path(suite).stem,[str(build/'qore'),'-b','--enable-debug',str(repo/'examples/test/qore'/suite),'-v'])
 return mode,0
status={'exit_code':1,'pid':os.getpid()};(out/'status.json').write_text(json.dumps(status,indent=2)+'\n')
try:
 with ThreadPoolExecutor(max_workers=2) as pool:status['modes']=dict(pool.map(qualify,['Debug','Release']))
 assert pins=={n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in paths}
 status['exit_code']=0
except BaseException as error:
 status['error']=repr(error);raise
finally:(out/'status.json').write_text(json.dumps(status,indent=2)+'\n')
