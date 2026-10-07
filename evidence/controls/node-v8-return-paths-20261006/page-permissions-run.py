# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import json,resource,signal,subprocess
from pathlib import Path
resource.setrlimit(resource.RLIMIT_CORE,(0,0)); w=Path('/fixture')
flags=json.loads(Path('/flags/obs-compile-flags.json').read_text())
for kind in ['original','fixed']:
 r=subprocess.run(['g++',*flags,'-c',str(w/(kind+'.cc')),'-o',str(w/(kind+'.o'))],capture_output=True,text=True)
 (w/(kind+'-compile.log')).write_text(r.stdout+r.stderr)
 if kind=='original':assert r.returncode and 'control reaches end of non-void function' in r.stderr,(r.returncode,r.stderr)
 else:assert r.returncode==0 and not r.stderr,(r.returncode,r.stderr)
 print(kind,'OBS compile expectation passed',flush=True)
subprocess.run(['g++',*flags,'-ffunction-sections','-fdata-sections',str(w/'fixed.cc'),'/sources/nodejs24-page-permissions-test.cc','-Wl,--gc-sections','-lnode','-pthread','-o',str(w/'control')],check=True)
subprocess.run([str(w/'control')],check=True)
for value in ['-1','5','255','256','2147483647','-2147483648']:
 for pair in [(value,'0'),('0',value)]:
  r=subprocess.run([str(w/'control'),*pair],capture_output=True,text=True)
  assert r.returncode==-signal.SIGABRT and 'unreachable code' in r.stderr,(pair,r)
  print('Invalid pair rejected:',pair,flush=True)
for args in [[''],['4extra','0'],['2147483648','0'],['0','-2147483649'],['0','0','extra']]:
 r=subprocess.run([str(w/'control'),*args],capture_output=True,text=True)
 assert r.returncode==2 and not r.stderr,(args,r)
# The declaration-only CPU fix must preserve object code with detection enabled,
# disabled, and the generic V8 build. It must remove only the generic warning.
common=['gcc','-O2','-Wall','-Wextra','-Werror','-fPIC','-I/v8/third_party/zlib','-I/v8/third_party/zlib/google']
for mode,defs in [('generic',[]),('disabled',['-DCPU_NO_SIMD']),('x86',['-DX86_NOT_WINDOWS','-DADLER32_SIMD_SSSE3'])]:
 for kind in ['original','fixed']:
  obj=w/(mode+'-'+kind+'.o')
  r=subprocess.run([*common,*defs,*(['-Wno-error=unused-function'] if kind=='original' and mode=='generic' else []),'-c',str(w/('cpu-'+kind+'.c')),'-o',str(obj)],capture_output=True,text=True)
  (w/(mode+'-'+kind+'.log')).write_text(r.stdout+r.stderr)
  assert r.returncode==0,(mode,kind,r.stderr)
  if kind=='original' and mode=='generic':assert 'declared' in r.stderr and 'never defined' in r.stderr,r.stderr
  else:assert not r.stderr,r.stderr
  for section in ['.text','.data','.bss']:
   subprocess.run(['objcopy','-O','binary','--only-section='+section,str(obj),str(w/(mode+'-'+kind+section))],check=True)
 for section in ['.text','.data','.bss']:
  assert (w/(mode+'-original'+section)).read_bytes()==(w/(mode+'-fixed'+section)).read_bytes(),(mode,section)
 print('CPU code unchanged and warning-free:',mode,flush=True)
subprocess.run([*common,str(w/'cpu-test.c'),str(w/'x86-fixed.o'),'-pthread','-o',str(w/'cpu-control')],check=True)
subprocess.run([str(w/'cpu-control')],check=True)
for binary in ['cpu-control','control']:
 subprocess.run(['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=definite,indirect,possible','--log-file='+str(w/(binary+'-valgrind.log')),str(w/binary)],check=True)
print('Permission and CPU controls pass',flush=True)
