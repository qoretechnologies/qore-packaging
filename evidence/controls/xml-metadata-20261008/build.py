# Copyright (C) 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json,os,subprocess
r=Path.cwd();source=r/'work/xml-metadata-candidate-20261008';images={t:json.loads((r/f'results/{t}-xml-final-build-2/build.json').read_text())['image'] for t in ('fedora','leap','el10')}
assert json.loads((r/'results/xml-metadata-unit-final2-20261008/status.json').read_text())==dict.fromkeys(images,0)
manifest=json.loads((source/'source-manifest.json').read_text());previous=json.loads((r/'work/xml-final-source-1/source-manifest.json').read_text())
assert manifest['candidate'] and len(manifest['packaging_overlay'])==4
assert manifest['components']==previous['components'] and manifest['sources']['libxml2-2.15.4.tar.xz']==previous['sources']['libxml2-2.15.4.tar.xz']
out=r/'results/xml-metadata-build2-status-20261008.json';state={'source':str(source.relative_to(r)),'images':images,'pid':os.getpid(),'results':{}};out.write_text(json.dumps(state,indent=2)+'\n')
def run(t):
 with (r/f'results/{t}-xml-metadata-driver2-20261008.log').open('x') as log:res=subprocess.run(['python3','-B','-W','error','tools/build-local.py','--source',str(source),'--image',images[t],'--output',f'results/{t}-xml-metadata-candidate-20261008','--jobs','2','--keep-build'],stdout=log,stderr=subprocess.STDOUT)
 print(t,res.returncode,flush=True);return t,res.returncode
with ThreadPoolExecutor(max_workers=3) as pool:
 for t,code in pool.map(run,images):state['results'][t]=code;out.write_text(json.dumps(state,indent=2)+'\n')
state['exit_code']=int(any(state['results'].values()));out.write_text(json.dumps(state,indent=2)+'\n');raise SystemExit(state['exit_code'])
