# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,re,shlex,subprocess
root=Path.cwd();source=root/'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
out=root/'results/node-arm-header-20261008';out.mkdir();fixed=root/'work/node-arm-header-20261008';fixed.mkdir()
header='deps/v8/src/regexp/arm64/regexp-macro-assembler-arm64.h';impl='deps/v8/src/regexp/arm64/regexp-macro-assembler-arm64.cc'
for rel,old,new in [(header,'Operand extra_space = Operand(0));','Operand extra_space);'),(impl,'CallCheckStackGuardState(x10);','CallCheckStackGuardState(x10, Operand(0));')]:
 text=(source/rel).read_text();assert text.count(old)==1;(fixed/Path(rel).name).write_text(text.replace(old,new))
(out/'header-probe.cc').write_text('// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT\n#include "src/regexp/arm64/regexp-macro-assembler-arm64.h"\n')
log=(root/'results/node-native-rev5-live-20261008/aarch64-snapshot3.log').read_text().splitlines()
line=next(l for l in log if 'g++ -o' in l and '../deps/v8/src/regexp/regexp.cc ' in l)
args=shlex.split(re.sub(r'^\[\s*\d+s\]\s+','',line));args[2:4]=['/control/probe.o','/control/header-probe.cc']
pos=args.index('-MF');del args[pos:pos+2]
args=[a for a in args if a not in ['-MMD','-flto=4','-ffat-lto-objects','-mbranch-protection=standard']]
args=[a.replace('/home/abuild/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1','/source') for a in args]
args+=['-Werror']
records=[]
for name in ['original','fixed']:
 cmd=['docker','run','--rm','--network','none','--user','1019:100','-v',str(source)+':/source:ro','-v',str(out)+':/control']
 if name=='fixed':cmd+=['-v',str(fixed/Path(header).name)+':/source/'+header+':ro']
 cmd+=['-w','/source/out','sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414',*args]
 with (out/(name+'.log')).open('x') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 records.append({'mode':name,'command':cmd,'exit_code':r.returncode})
 print(name,r.returncode,(out/(name+'.log')).read_text()[-2500:],flush=True)
(out/'status.json').write_text(json.dumps(records,indent=2)+'\n')
