# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,shlex,subprocess
root=Path('/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1');out=Path('/control')
line=next(l for l in Path('/work/build.log').read_text().splitlines() if l.strip().startswith('g++ -o ') and 'raw-machine-assembler.o ' in l)
args=shlex.split(line);args[2]='/control/control.o';args[3]='/control/control.cc'
# Retain ABI/feature definitions; use native sections from the fat LTO archives.
args=[a for a in args if not a.startswith('-flto=') and a!='-ffat-lto-objects'];args += ['-fno-lto']; args[args.index('-MF')+1]='/control/control.d'
cmds=[('compile',args),('link',['g++','-fno-lto','-pthread','-Wl,--gc-sections','/control/control.o','-Wl,--start-group',*[str(root/'out/Release/obj.target/tools/v8_gypfiles'/n) for n in ('libv8_compiler.a','libv8_base_without_compiler.a','libv8_libbase.a','libabseil.a','libv8_zlib.a','libhighway.a','libsimdutf.a')],'-Wl,--end-group','-lz','-licui18n','-licuuc','-ldl','-lrt','-o','/control/original'])]
records=[]
for name,cmd in cmds:
 with (out/(name+'3.log')).open('x') as log:r=subprocess.run(cmd,cwd=root/'out',stdout=log,stderr=subprocess.STDOUT)
 records.append({'name':name,'exit_code':r.returncode,'command':cmd});(out/'status3.json').write_text(json.dumps(records,indent=2)+'\n');r.check_returncode()
