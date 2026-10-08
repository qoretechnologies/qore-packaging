# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,re,shlex,subprocess
root=Path.cwd();source=root/'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1';fixed=root/'work/node-arm-header-20261008'
out=root/'results/node-arm-header-codegen-20261008';out.mkdir()
header='deps/v8/src/regexp/arm64/regexp-macro-assembler-arm64.h';impl='deps/v8/src/regexp/arm64/regexp-macro-assembler-arm64.cc'
line=next(l for l in (root/'results/node-native-rev5-live-20261008/aarch64-snapshot3.log').read_text().splitlines() if 'g++ -o' in l and '../'+impl+' ' in l)
base=shlex.split(re.sub(r'^\[\s*\d+s\]\s+','',line));pos=base.index('-MF');del base[pos:pos+2]
base=[a for a in base if a not in ['-MMD','-flto=4','-ffat-lto-objects','-mbranch-protection=standard']]
base=[a.replace('/home/abuild/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1','/source') for a in base]
image='sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414';records=[]
def run(name,args,patched=True):
 cmd=['docker','run','--rm','--network','none','--user','1019:100','-v',str(source)+':/source:ro','-v',str(out)+':/control','-v',str(root/'work/node-arm-operand-control-20261008.cc')+':/operand.cc:ro']
 if patched:
  for rel in [header,impl]:cmd+=['-v',str(fixed/Path(rel).name)+':/source/'+rel+':ro']
 cmd+=['-w','/source/out',image,*args]
 with (out/(name+'.log')).open('x') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 records.append({'name':name,'command':cmd,'exit_code':r.returncode})
 (out/'status.json').write_text(json.dumps(records,indent=2)+'\n')
 print(name,r.returncode,flush=True)
 return r.returncode
for mode in ['original','fixed']:
 args=base.copy();args[2]='/control/'+mode+'.o';args+=['-g0']
 assert run(mode,args,mode=='fixed')==0
# Strip non-runtime symbol-table file names before comparing generated sections.
for name in ['original','fixed']:
 assert run(name+'-objcopy',['objcopy','--strip-debug','--remove-section=.comment','/control/'+name+'.o','/control/'+name+'-code.o'])==0
same=(out/'original-code.o').read_bytes()==(out/'fixed-code.o').read_bytes()
(out/'code-identity.json').write_text(json.dumps({'identical':same,'sha256':{name:hashlib.sha256((out/(name+'-code.o')).read_bytes()).hexdigest() for name in ['original','fixed']}},indent=2)+'\n')
print('code identity',same,flush=True)
args=base.copy();args[2:4]=['/control/operand.o','/operand.cc'];args+=['-Werror']
assert run('operand-build',args)==0
assert run('operand-link',['g++','-pthread','/control/operand.o','-o','/control/operand'])==0
assert run('operand',['/control/operand'])==0
assert run('operand-valgrind',['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','/control/operand'])==0
assert same
