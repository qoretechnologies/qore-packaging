# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,shlex,subprocess
root=Path('/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1');out=Path('/control')
s=(root/'deps/v8/src/api/api.cc').read_text();header=s[:s.index('namespace v8 {')]
a=s.index('v8::String::ExternalStringResourceBase* GetExternalResourceFromForwardingTable(');b=s.index('\n}  // namespace',a);helper=s[a:b]
a=s.index('void v8::String::VerifyExternalStringResource(');b=s.index('\nvoid v8::String::VerifyExternalStringResourceBase(',a);body=s[a:b]
old='''      if (!is_one_byte) {
        expected = reinterpret_cast<const ExternalStringResource*>(resource);
      }'''
new='''      expected = is_one_byte
                     ? nullptr
                     : reinterpret_cast<const ExternalStringResource*>(resource);'''
assert body.count(old)==1
body=body.replace(old,new)
(out/'fixed.cc').write_text(header+'namespace v8 {\nnamespace {\n'+helper+'\n}\n'+body+'\n}\n')
line=next(l for l in Path('/work/build.log').read_text().splitlines() if l.strip().startswith('g++ -o ') and '/src/api/api.o ' in l)
args=shlex.split(line);args[2]='/control/fixed.o';args[3]='/control/fixed.cc'
args=[a for a in args if not a.startswith('-flto=') and a!='-ffat-lto-objects'];args+=['-fno-lto'];args[args.index('-MF')+1]='/control/fixed.d'
commands=[('fixed-compile',args),('fixed-link',['g++','-std=c++20','-O2','-g','-Wall','-Wextra','-Werror','-isystem','/usr/include/node','/control/control3.cc','/control/fixed.o','-lnode','-pthread','-Wl,--export-dynamic-symbol=_ZNK2v86String28VerifyExternalStringResourceEPNS0_22ExternalStringResourceE','-o','/control/fixed']),('fixed-ordinary',['/control/fixed','ordinary']),('fixed-shared',['/control/fixed','shared'])]
records=[]
for name,cmd in commands:
 with (out/(name+'.log')).open('x') as log:r=subprocess.run(cmd,cwd=root/'out',stdout=log,stderr=subprocess.STDOUT)
 records.append(dict(name=name,command=cmd,exit_code=r.returncode));(out/'fixed-status.json').write_text(json.dumps(records,indent=2)+'\n');r.check_returncode()
