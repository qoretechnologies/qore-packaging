# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import importlib.util,json,subprocess
root=Path.cwd();repo=root/'work/jni-rpm-integration-1'
loader=importlib.util.spec_from_file_location('packaging',root/'tools/packaging.py');m=importlib.util.module_from_spec(loader);loader.loader.exec_module(m)
output=root/'work/jni-rpm-metadata-candidate-20261007'
m.prepare_source(repo,'33367ce003ecf29b0a2a84964ab913146837d6d0','qore-jni-module','2.7.0',output,
 exclusions=['test/kotlin-test.jar','test/opcua-test-server.jar','src/java/org/qore/lang/JdbcDatasource.class'],
 packaging_overlay=repo,spec_path='qore-jni-module.spec',vendor_manifest='rpm/vendor-sources.json',cache=root/'cache')
def build(target):
 image=json.loads((root/f'results/{target}-jni-rpm-final-3/build.json').read_text())['image']
 with (root/f'results/{target}-jni-rpm-metadata-candidate-driver-20261007.log').open('x') as log:
  r=subprocess.run(['python3','-B','-W','error','tools/build-local.py','--source',str(output),'--image',image,
    '--output',f'results/{target}-jni-rpm-metadata-candidate-20261007','--jobs','2','--internal-interface','--keep-build'],stdout=log,stderr=subprocess.STDOUT)
 return target,r.returncode
with ThreadPoolExecutor(max_workers=3) as pool:result=dict(pool.map(build,('fedora','leap','el10')))
(root/'results/jni-rpm-metadata-candidate-status-20261007.json').write_text(json.dumps(result,indent=2)+'\n')
print(result,flush=True)
raise SystemExit(any(result.values()))
