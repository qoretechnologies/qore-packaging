# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
w=Path('/fixture');s='/source/deps/v8/src/heap/base/asm/x64/push_registers_asm.cc'
flags=['g++','-O2','-Wall','-Wextra','-Werror','-g','-fPIC','-fstack-protector-strong']
def run(args,name,expected=0):
 r=subprocess.run(args,capture_output=True,text=True);(w/name).write_text(r.stdout+r.stderr)
 assert r.returncode==expected,(args,r.returncode,r.stderr[-4000:]);return r.stdout+r.stderr
run([*flags,'-flto=auto','-c',s,'-o','/fixture/broken.o'],'broken-compile.log')
run(['gcc-ar','rcs','/fixture/libbroken.a','/fixture/broken.o'],'broken-archive.log')
r=run([*flags,'-flto=auto','/fixture/control.cc','/fixture/libbroken.a','-o','/fixture/broken'],'broken-link.log',1)
assert 'undefined reference to `PushAllRegistersAndIterateStack' in r,r
run([*flags,'-flto=4','-ffat-lto-objects','-fno-lto','-c',s,'-o','/fixture/native.o'],'native-compile.log')
run(['gcc-ar','rcs','/fixture/libnative.a','/fixture/native.o'],'native-archive.log')
run([*flags,'-flto=4','-ffat-lto-objects','/fixture/control.cc','/fixture/libnative.a','-o','/fixture/control'],'native-link.log')
run(['/fixture/control'],'native.log')
run(['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','--log-file=/fixture/valgrind.log','/fixture/control'],'valgrind-stdout.log')
run(['readelf','-Ws','/fixture/native.o'],'native-symbols.log')
run(['readelf','-Ws','/fixture/broken.o'],'broken-symbols.log')
print('Negative LTO link reproduced; native assembly plus LTO caller passes native/Valgrind',flush=True)
