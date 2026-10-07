# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import re
import subprocess
root=Path.cwd();build=root/'results/leap-nodejs24-canonical-final-20261007'
record=json.loads((build/'build.json').read_text())
source='/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
out=root/'results/node-bundled-headers-memory-20261007';out.mkdir()
rows=[]
for name in ['platform-priority-control','allocation-status-control','page-permissions-control']:
    binary=build/source.removeprefix('/work/')/'out'/name
    assert binary.is_file()
    cmd=['docker','run','--rm','--init','--network','none','-v',str(build)+':/work:ro','-w',source,
         record['image'],'valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all',
         '--errors-for-leak-kinds=definite,indirect,possible','out/'+name]
    with (out/(name+'.log')).open('x') as log:
        result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=240)
    text=(out/(name+'.log')).read_text();rows.append({'name':name,'command':cmd,'exit_code':result.returncode})
    (out/'status.json').write_text(json.dumps(rows,indent=2)+'\n')
    assert result.returncode==0 and 'ERROR SUMMARY: 0 errors' in text,text[-4000:]
    assert not re.search(r'(?i)warning:|FAIL',text),text[-3000:]
    assert 'All heap blocks were freed -- no leaks are possible' in text or all(re.search(kind+r' lost:\s+0 bytes in 0 blocks',text) for kind in ['definitely','indirectly','possibly'])
    print(name,'PASS',flush=True)
