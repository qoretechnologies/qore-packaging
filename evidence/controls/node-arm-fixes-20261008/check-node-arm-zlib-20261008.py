# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,subprocess
root=Path.cwd();source=root/'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
out=root/'results/node-arm-zlib-20261008';out.mkdir();fixed=root/'work/node-arm-zlib-20261008';fixed.mkdir()
rel='deps/v8/third_party/zlib/cpu_features.c';text=(source/rel).read_text()
old='#if (defined(__ARM_NEON__) || defined(__ARM_NEON))\n#if !defined(ARMV8_OS_MACOS)'
new='''#if (defined(__ARM_NEON__) || defined(__ARM_NEON))
#if !defined(ARMV8_OS_MACOS) && \\
    (defined(ARMV8_OS_ANDROID) || defined(ARMV8_OS_LINUX) || \\
     defined(ARMV8_OS_FUCHSIA) || defined(ARMV8_OS_WINDOWS) || \\
     defined(ARMV8_OS_IOS))'''
assert text.count(old)==1;(fixed/'cpu_features.c').write_text(text.replace(old,new))
image='sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414';records=[]
modes={'generic':[],'generic-neon':['-D__ARM_NEON'],'generic-neon-alt':['-D__ARM_NEON__'],'disabled-neon':['-D__ARM_NEON','-DCPU_NO_SIMD'],'macos-neon':['-D__ARM_NEON','-DARMV8_OS_MACOS'],'x86-detection':['-DX86_NOT_WINDOWS','-DADLER32_SIMD_SSSE3'],'riscv-detection':['-DRISCV_RVV']}
for mode,defines in modes.items():
 for version in ['original','fixed']:
  name=mode+'-'+version
  cmd=['docker','run','--rm','--network','none','--user','1019:100','-v',str(source)+':/source:ro','-v',str(out)+':/control']
  if version=='fixed':cmd+=['-v',str(fixed/'cpu_features.c')+':/source/'+rel+':ro']
  cmd+=[image,'gcc','-O2','-Wall','-Wextra']
  if version=='fixed' or mode not in ['generic-neon','generic-neon-alt']:cmd+=['-Werror']
  cmd+=[*defines,'-I/source/deps/v8/third_party/zlib','-c','/source/'+rel,'-o','/control/'+name+'.o']
  with (out/(name+'.log')).open('x') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
  records.append({'name':name,'command':cmd,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(records,indent=2)+'\n')
  print(name,r.returncode,flush=True)
  assert r.returncode==0,(out/(name+'.log')).read_text()
  subprocess.run(['objcopy','--strip-debug','--remove-section=.comment',str(out/(name+'.o')),str(out/(name+'-code.o'))],check=True)
 a=(out/(mode+'-original-code.o')).read_bytes();b=(out/(mode+'-fixed-code.o')).read_bytes()
 assert a==b,mode
print('All seven configurations have identical generated code and data; fixed builds pass with all warnings treated as errors.')
