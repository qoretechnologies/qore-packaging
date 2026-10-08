# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,re,shlex,subprocess
root=Path.cwd();source=root/'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1';fixed=root/'work/node-arm-initialization-20261008/assembler-arm64.h';out=root/'work/node-arm-initialization-objects-20261008';out.mkdir()
raw=(root/'results/node-native-rev5-live-20261008/aarch64-final.log').read_text().splitlines();records=[]
for stem,rel in [('macro-assembler','deps/v8/src/codegen/arm64/macro-assembler-arm64.cc'),('code-generator','deps/v8/src/compiler/backend/arm64/code-generator-arm64.cc')]:
 line=next(l for l in raw if 'g++ -o' in l and '../'+rel+' ' in l)
 base=shlex.split(re.sub(r'^\[\s*\d+s\]\s+','',line));pos=base.index('-MF');del base[pos:pos+2]
 base=[a for a in base if a not in ['-MMD','-flto=4','-ffat-lto-objects','-mbranch-protection=standard']]
 base=[a.replace('/home/abuild/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1','/source') for a in base]
 for mode in ['original','fixed']:
  args=base.copy();args[2]='/control/'+stem+'-'+mode+'.o';args+=['-g0','-fno-lto']
  cmd=['docker','run','--rm','--network','none','--user','1019:100','-v',str(source)+':/source:ro','-v',str(out)+':/control']
  if mode=='fixed':cmd+=['-v',str(fixed)+':/source/deps/v8/src/codegen/arm64/assembler-arm64.h:ro']
  cmd+=['-w','/source/out','sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414',*args]
  with (out/(stem+'-'+mode+'.log')).open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  records.append({'name':stem+'-'+mode,'command':cmd,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(records,indent=2)+'\n');r.check_returncode();print(stem,mode,'done',flush=True)
