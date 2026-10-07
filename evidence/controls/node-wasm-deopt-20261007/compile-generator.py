# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,shlex,subprocess
root=Path('/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1');out=Path('/control')
receipts=list((root/'out/Release/.deps').rglob('code-generator.o.d'));assert len(receipts)==1
args=shlex.split(receipts[0].read_text().splitlines()[0].split(' := ',1)[1]);args=[a for a in args if not a.startswith('-flto') and a!='-ffat-lto-objects'];args+=['-fno-lto']
records=[]
for name in ('original','fixed'):
 cmd=list(args);cmd[2]='/control/'+name+'-generator.o';cmd[cmd.index('-MF')+1]='/control/'+name+'-generator.d'
 if name=='fixed':cmd[3]='/control/proposed/src/compiler/backend/code-generator.cc';cmd[1:1]=['-I/control/proposed']
 with (out/(name+'-generator-compile.log')).open('w') as log:r=subprocess.run(cmd,cwd=root/'out',stdout=log,stderr=subprocess.STDOUT)
 records.append(dict(name=name,exit_code=r.returncode,command=cmd));(out/'generator-status.json').write_text(json.dumps(records,indent=2)+'\n');r.check_returncode()
print('Both actual generator files compiled.')
