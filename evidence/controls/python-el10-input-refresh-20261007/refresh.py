# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys,urllib.request,xml.etree.ElementTree as ET
root=Path.cwd();out=root/'results/python-el10-input-refresh-20261007';out.mkdir(exist_ok=True)
p=root/'qualification/python-el10-aarch64.json';manifest=json.loads(p.read_text());records=[];listings={};history={}
sources=json.loads((root/'results/python-native-inputs-20261007/sources.json').read_text())
for package in manifest['packages']:
 base=package['url'].rsplit('/',1)[0];api=base.removeprefix('https://api.opensuse.org/public')
 if base not in listings:
  listings[base]=ET.fromstring(subprocess.check_output(['osc','--setopt','http_retries=1','api',api],timeout=120))
  history[base]=ET.fromstring(subprocess.check_output(['osc','--setopt','http_retries=1','api',api+'/_history'],timeout=120))[-1].attrib
  source_package=base.rsplit('/',1)[1]
  if source_package=='qore':assert history[base]['srcmd5']==manifest['obs_srcmd5'],history[base]
  if source_package in ('qore-xml-module','qore-python-module'):
   name=source_package.removeprefix('qore-').removesuffix('-module');assert history[base]['srcmd5']==sources[name]['srcmd5']
 names=[e.get('filename') for e in listings[base] if e.get('filename','').endswith(('.aarch64.rpm','.noarch.rpm')) and e.get('filename','').rsplit('-',2)[0]==package['name']]
 name,=names
 assert name.rsplit('-',2)[1]==package['filename'].rsplit('-',2)[1],(name,package['filename'])
 url=base+'/'+name
 with urllib.request.urlopen(url,timeout=120) as response:data=response.read()
 digest=hashlib.sha256(data).hexdigest();(out/name).write_bytes(data)
 old=package.copy();package.update(filename=name,url=url,sha256=digest)
 records.append({'before':old,'after':package.copy(),'history':history[base]})
sys.path.insert(0,str(root/'tools'));s=importlib.util.spec_from_file_location('q',root/'tools/qualify-installed.py');q=importlib.util.module_from_spec(s);s.loader.exec_module(q);q.validate(manifest)
p.write_text(json.dumps(manifest,indent=2)+'\n');(out/'review.json').write_text(json.dumps(records,indent=2)+'\n')
print('Verified',len(records),'current RPMs;',sum(r['before']!=r['after'] for r in records),'pins refreshed; source versions unchanged')
