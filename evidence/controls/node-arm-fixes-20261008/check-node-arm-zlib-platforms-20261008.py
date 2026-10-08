# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import itertools,json,subprocess
root=Path.cwd();source=root/'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1';out=root/'results/node-arm-zlib-platforms-20261008';out.mkdir()
for rel in ['cpu-features.h','asm/hwcap.h','zircon/features.h','zircon/syscalls.h','zircon/types.h','windows.h','sys/sysctl.h']:
 p=out/'include'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('/* Copyright 2026 Qore Technologies, s.r.o.; MIT. Preprocessor-only SDK placeholder. */\n')
platforms=['ANDROID','LINUX','FUCHSIA','WINDOWS','IOS','MACOS'];cases=[]
for platform,neon,arch64,disabled in itertools.product(platforms,['__ARM_NEON','__ARM_NEON__'],[False,True],[False,True]):
 name=f'{platform}-{neon}-{int(arch64)}-{int(disabled)}'
 defines=['-DARMV8_OS_'+platform,'-D'+neon]+(['-D__aarch64__'] if arch64 else [])+(['-DCPU_NO_SIMD'] if disabled else [])
 cases.append({'name':name,'defines':defines})
(out/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
script='''from pathlib import Path
import json,subprocess,sys
mode=sys.argv[1]
for case in json.loads(Path('/control/cases.json').read_text()):
 cmd=['gcc','-E','-P','-I/control/include','-I/source/deps/v8/third_party/zlib',*case['defines'],'/source/deps/v8/third_party/zlib/cpu_features.c']
 r=subprocess.run(cmd,text=True,capture_output=True)
 assert r.returncode==0 and not r.stderr,(case,r.stderr)
 Path('/control/'+mode+'-'+case['name']+'.i').write_text(r.stdout)
print(len(json.loads(Path('/control/cases.json').read_text())), 'preprocessor configurations pass',flush=True)
'''
records=[]
for mode in ['original','fixed']:
 cmd=['docker','run','--rm','--network','none','--user','1019:100','-v',str(source)+':/source:ro','-v',str(out)+':/control']
 if mode=='fixed':cmd+=['-v',str(root/'work/node-arm-zlib-20261008/cpu_features.c')+':/source/deps/v8/third_party/zlib/cpu_features.c:ro']
 cmd+=['sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414','python3','-c',script,mode]
 with (out/(mode+'.log')).open('x') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 records.append({'mode':mode,'exit_code':r.returncode,'command':cmd});(out/'status.json').write_text(json.dumps(records,indent=2)+'\n');r.check_returncode()
for case in cases:assert (out/('original-'+case['name']+'.i')).read_bytes()==(out/('fixed-'+case['name']+'.i')).read_bytes(),case
(out/'comparison.json').write_text(json.dumps({'configurations':len(cases),'preprocessed_sources_identical':True,'limits':'Unavailable platform SDK headers are empty placeholders for preprocessing only. This verifies conditional selection and retained source tokens, not execution on those operating systems.'},indent=2)+'\n')
print('All',len(cases),'selected ARM-platform configurations retain identical preprocessed code.')
