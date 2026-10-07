# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import concurrent.futures,hashlib,importlib.util,json,subprocess,sys,urllib.request,xml.etree.ElementTree as ET
root=Path.cwd();project='home:davidnichols:qore:testing';out=root/'results/python-native-inputs-20261007';out.mkdir(exist_ok=True)
sys.path.insert(0,str(root/'tools'));spec=importlib.util.spec_from_file_location('qualify',root/'tools/qualify-installed.py');qualify=importlib.util.module_from_spec(spec);spec.loader.exec_module(qualify)
catalog=json.loads((root/'catalog.json').read_text())['packages'];sources={}
def api(path):return subprocess.check_output(['osc','--setopt','http_retries=1','api',path],timeout=120)
for name in ('xml','python'):
 base=f'/source/{project}/qore-{name}-module';manifest=json.loads(api(base+'/source-manifest.json'));data=api(base);(out/(name+'-source.xml')).write_bytes(data);listing=ET.fromstring(data)
 assert manifest['commit']==catalog['module-'+name]['commit']
 assert not manifest.get('candidate');sources[name]={'commit':manifest['commit'],'srcmd5':listing.get('srcmd5')}
modules=[]
for name in ('python',):
 commit=sources[name]['commit'];fixtures=[]
 for path in sorted(qualify.MODULE_FIXTURES[name]):
  expected=subprocess.check_output(['git','-C',str(root.parent/('module-'+name)),'show',commit+':'+path]);url=f'https://raw.githubusercontent.com/qoretechnologies/module-{name}/{commit}/{path}'
  with urllib.request.urlopen(url,timeout=60) as response:data=response.read()
  assert data==expected,(name,path);fixtures.append({'path':path,'url':url,'sha256':hashlib.sha256(data).hexdigest()})
 modules.append({'name':name,'commit':commit,'fixtures':fixtures})
def prepare(item):
 target,repository=item;manifest=json.loads((root/f'qualification/core21-{target}-aarch64.json').read_text());directory=out/target;directory.mkdir(exist_ok=True)
 for name in ('xml','python'):
  package='qore-'+name+'-module';base=f'/build/{project}/{repository}/aarch64/{package}'
  data=api(base+'/_history');(directory/(name+'-history.xml')).write_bytes(data);assert ET.fromstring(data)[-1].get('srcmd5')==sources[name]['srcmd5'],(target,name,ET.fromstring(data)[-1].attrib)
  data=api(base);(directory/(name+'-binaries.xml')).write_bytes(data)
  filenames=[e.get('filename') for e in ET.fromstring(data) if e.get('filename','').startswith(package+'-') and e.get('filename','').endswith('.aarch64.rpm') and '-debug' not in e.get('filename','')];assert len(filenames)==1,filenames
  filename=filenames[0];data=api(base+'/'+filename);(directory/filename).write_bytes(data)
  manifest['packages'].append({'name':package,'url':'https://api.opensuse.org/public'+base+'/'+filename,'filename':filename,'sha256':hashlib.sha256(data).hexdigest(),'phase':'runtime'})
 manifest['modules']=modules;qualify.validate(manifest)
 (root/f'qualification/python-{target}-aarch64.json').write_text(json.dumps(manifest,indent=2)+'\n');return target
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:print(list(pool.map(prepare,[('fedora','Fedora_44'),('leap','openSUSE_Leap_16.0'),('el10','AlmaLinux_10')])))
(out/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
