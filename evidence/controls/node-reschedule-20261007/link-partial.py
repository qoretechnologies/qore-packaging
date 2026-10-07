# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
root=Path('/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1');out=Path('/control');release=root/'out/Release'
records=[]
def run(name,cmd):
 with (out/(name+'.log')).open('x') as log:r=subprocess.run(cmd,cwd=root/'out',stdout=log,stderr=subprocess.STDOUT)
 records.append(dict(name=name,command=cmd,exit_code=r.returncode));(out/'partial-status.json').write_text(json.dumps(records,indent=2)+'\n');r.check_returncode()
archives=[]
for group in ['v8_compiler','v8_base_without_compiler']:
 # GYP writes the final .d receipt only after a successful object compile.
 # This is a fresh build tree, so these objects will not be rebuilt here.
 objs=[]
 for obj in sorted((release/'obj.target'/group).rglob('*.o')):
  receipt=release/'.deps'/str(obj).lstrip('/')
  if receipt.with_suffix('.o.d').exists():objs.append(str(obj))
 assert objs,group
 archive=out/(group+'-completed.a');archives.append(str(archive))
 run(group+'-archive',['ar','rcsT',str(archive),*objs])
base=release/'obj.target/tools/v8_gypfiles'
link=['g++','-fno-lto','-pthread','-Wl,--gc-sections','/control/control.o','-Wl,--start-group',*archives,*[str(base/n) for n in ['libv8_libbase.a','libabseil.a','libv8_zlib.a','libhighway.a','libsimdutf.a']],'-Wl,--end-group','-lz','-licui18n','-licuuc','-ldl','-lrt','-o','/control/original']
run('partial-link',link)
run('partial-normal',['/control/original'])
run('partial-memory',['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/control/partial-valgrind.log','/control/original'])
