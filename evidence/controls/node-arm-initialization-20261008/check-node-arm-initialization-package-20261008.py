# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,re,shlex,subprocess
root=Path.cwd();source=root/'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1';fixed=root/'work/node-arm-header-20261008'
out=root/'results/node-arm-initialization-package-control-20261008';out.mkdir()
rel='deps/v8/src/regexp/arm64/regexp-macro-assembler-arm64.cc'
line=next(l for l in (root/'results/node-native-rev5-live-20261008/aarch64-snapshot3.log').read_text().splitlines() if 'g++ -o' in l and '../'+rel+' ' in l)
args=shlex.split(re.sub(r'^\[\s*\d+s\]\s+','',line))
args=[a.replace('/home/abuild/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1','/source') for a in args if a!='-mbranch-protection=standard']
receipt='cmd_'+args[2]+' := '+shlex.join(args)+'\n'
p=out/'tree/out/Release/.deps/regexp-macro-assembler-arm64.o.d';p.parent.mkdir(parents=True);p.write_text(receipt)
(out/'tree/deps').symlink_to('/source/deps')
image='sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414';records=[]
for mode in ['original','fixed']:
 cmd=['docker','run','--rm','--network','none','--user','1019:100','-v',str(source)+':/source:ro','-v',str(out)+':/control','-v',str(root/'dependencies')+':/packaging:ro']
 for name in ['regexp-macro-assembler-arm64.h','regexp-macro-assembler-arm64.cc']:
  cmd+=['-v',str(fixed/name)+':/source/deps/v8/src/regexp/arm64/'+name+':ro']
 if mode=='fixed':cmd+=['-v',str(root/'work/node-arm-initialization-20261008/assembler-arm64.h')+':/source/deps/v8/src/codegen/arm64/assembler-arm64.h:ro']
 cmd+=[image,'python3','/packaging/nodejs24-arm-header-test.py','--source','/control/tree','--test-source','/packaging/nodejs24-arm-operand-test.cc','--initialization-test-source','/packaging/nodejs24-arm-initialization-test.cc','--output','/control/'+mode+'-operand']
 with (out/(mode+'.log')).open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 records.append({'name':mode,'exit_code':r.returncode,'command':cmd});(out/'status.json').write_text(json.dumps(records,indent=2)+'\n')
 assert r.returncode==(1 if mode=='original' else 0),(mode,(out/(mode+'.log')).read_text())
 if mode=='original':assert 'FAIL Operand immediate inactive fields' in (out/(mode+'.log')).read_text()
 else:assert (out/(mode+'.log')).read_text()=='PASS: 4491 actual ARM64 Operand checks\nPASS: 459 constructor/copy field checks\n'
 print(mode,r.returncode,flush=True)
for executable in ['fixed-operand','fixed-operand-initialization']:
 cmd=['docker','run','--rm','--network','none','--user','1019:100','-v',str(out)+':/control:ro',image,'valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','/control/'+executable]
 with (out/(executable+'-valgrind.log')).open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 records.append({'name':executable+'-valgrind','exit_code':r.returncode,'command':cmd});(out/'status.json').write_text(json.dumps(records,indent=2)+'\n');r.check_returncode()
print('Package helper rejects original inactive fields; both fixed controls pass normally/Valgrind.')
