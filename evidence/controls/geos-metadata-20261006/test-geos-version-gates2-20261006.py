# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json,subprocess
root=Path.cwd();images=json.loads((root/'results/geos-sdk-docs-images-20261006.json').read_text())
def run(target):
 out=root/f'results/{target}-geos-version-gates2-20261006';out.mkdir()
 paths=[p for p in (root/f'results/{target}-geos-metadata-candidate3-20261006/rpmbuild/BUILD').rglob('geos-api-2.0.qmod') if 'BUILDROOT' not in p.parts];assert len(paths)==1;build=paths[0].parent
 commands=[]
 for mode in ('memory',):
  script='. /usr/lib/rpm/qore/module-env.sh\nexport QORE_MODULE_DIR="/module:$QORE_MODULE_DIR"\n'
  script+='pkg-config --modversion geos\n'
  script+=('valgrind --error-exitcode=99 --leak-check=full --show-leak-kinds=all --errors-for-leak-kinds=definite,indirect,possible --log-file=/results/valgrind.log ' if mode=='memory' else '')+'qore -b --enable-debug -l /module/geos-api-2.0.qmod /tests/geos-version-gates.qtest -v\n'
  cmd=['docker','run','--rm','--init','--network','none','--user','1019:100','-v',str(build)+':/module:ro','-v',str(root/'work/checkouts/module-geos-metadata-20261006/test')+':/tests:ro','-v',str(out)+':/results',images[target],'sh','-eu','-c',script]
  with (out/(mode+'.log')).open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  commands.append({'mode':mode,'command':cmd,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(commands,indent=2)+'\n')
  if r.returncode:return target,r.returncode
 return target,0
with ThreadPoolExecutor(max_workers=3) as p:print(dict(p.map(run,images)))
