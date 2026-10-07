# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
root=Path.cwd();build=root/'results/leap-nodejs24-canonical-final-20261007';out=root/'results/node-canonical-final-memory-20261007';out.mkdir()
source='/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
assert json.loads((build/'build.json').read_text())['exit_code'] == 0
assert (build/source.removeprefix('/work/')/'out/wasm-deopt-control').is_file(), 'retained native test binary missing'
records=[]
for name,args in [('wasm-deopt',['out/wasm-deopt-control','positive']),('reschedule',['out/reschedule-control']),('timezone',['out/timezone-index-control/timezone-index']),('external-ordinary',['out/external-string-resource-control','ordinary']),('external-shared',['out/external-string-resource-control','shared'])]:
 cmd=['docker','run','--rm','--network','none','--user','1019:100','-e','HOME=/tmp','-e','LD_LIBRARY_PATH='+source+'/out/Release','-v',str(build)+':/work:ro','-v',str(out)+':/control','-w',source,'sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414','valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','--log-file=/control/'+name+'-valgrind.log',*args]
 with (out/(name+'.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 records.append({'name':name,'exit_code':r.returncode,'command':cmd});(out/'status.json').write_text(json.dumps(records,indent=2)+'\n')
print({x['name']:x['exit_code'] for x in records})

raise SystemExit(1 if any(x["exit_code"] for x in records) else 0)
