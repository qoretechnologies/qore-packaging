# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json,shutil,subprocess
root=Path.cwd();repo=root/'work/checkouts/qore-documentation-sdk-20261006';negative=root/'work/core-flex-source-path-20261007/original';(negative/'rpm/tests').mkdir(parents=True,exist_ok=True)
shutil.copy2(root/'work/core-flex-source-path-20261007/before/CMakeLists.txt',negative/'CMakeLists.txt');shutil.copy2(repo/'rpm/tests/test_flex_source_paths.py',negative/'rpm/tests/test_flex_source_paths.py')
out=root/'results/core-flex-source-path3-20261007';out.mkdir(exist_ok=True)
def run(target):
 image=json.loads((root/'results/core-flex-test-images-20261007/images.json').read_text())[target]['image'];records=[]
 for variant,source,expected in [('fixed',repo,0),('original',negative,1)]:
  command=['docker','run','--rm','--network','none','--user','1019:100','-e','HOME=/tmp','-v',str(source)+':/fixture:ro',image,'python3','-B','-W','error','/fixture/rpm/tests/test_flex_source_paths.py','-v']
  p=out/(target+'-'+variant+'.log')
  with p.open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
  records.append({'variant':variant,'exit_code':r.returncode,'command':command});assert r.returncode==expected,p.read_text()
  if variant=='original':assert "'lib/scanner.lpp' not found" in p.read_text(),p.read_text()
 return target,records
with ThreadPoolExecutor(max_workers=3) as pool:records=dict(pool.map(run,['fedora','leap','el10']))
(out/'results.json').write_text(json.dumps(records,indent=2)+'\n');print({t:{x['variant']:x['exit_code'] for x in v} for t,v in records.items()})
