# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
root=Path.cwd();out=root/'work/node-dns-fixtures-20261007';result=root/'results/leap-nodejs24-obs-flags-candidate7-20261007'
source='/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1';records=[]
for mode,count in [('fixed',1)]:
 for path in ['test/parallel/test-dns-setserver-when-querying.js','test/pummel/test-heapdump-dns.js']:
  for repeat in range(count):
   name=f'formatted-{mode}-{Path(path).stem}-{repeat}'
   cmd=['docker','run','--rm','--network','none','--user','1019:100','-e','LD_LIBRARY_PATH='+source+'/out/Release','-v',str(result)+':/work:ro']
   if mode=='fixed':cmd+=['-v',str(out/Path(path).name)+':'+source+'/'+path+':ro']
   cmd+=['-w',source,'sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414',source+'/out/Release/node',path]
   with (out/(name+'.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
   records.append(dict(name=name,command=cmd,exit_code=r.returncode));(out/'formatted-status.json').write_text(json.dumps(records,indent=2)+'\n')
   if mode=='fixed':r.check_returncode()
print('Finished',len(records),'DNS controls')
