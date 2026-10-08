# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse,hashlib,importlib.util,json,re,subprocess,sys,urllib.request,xml.etree.ElementTree as ET
root=Path.cwd();sys.path.insert(0,str(root/'tools'));spec=importlib.util.spec_from_file_location('installed',root/'tools/qualify-installed.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
parser=argparse.ArgumentParser();parser.add_argument('targets',nargs='+',choices=['fedora','el10','leap']);args=parser.parse_args()
commit='c008b67e10fe91c3c5268926f44f59c521babba5';expected='2f9526bbf3fc2b152ea2fce4bf451cf8';repo=root/'work/checkouts/module-grpc-native-dependencies-20261008';out=root/'results/grpc-arm-rev5-inputs-20261008';out.mkdir(exist_ok=True)
osc=['osc','--setopt','http_retries=1','-A','https://api.opensuse.org','api'];project='home:davidnichols:qore:testing'
fixture_file=out/'fixtures.json'
if fixture_file.exists():
 fixtures=json.loads(fixture_file.read_text());assert {p['path'] for p in fixtures}==mod.MODULE_FIXTURES['grpc']
 for p in fixtures:assert hashlib.sha256(subprocess.check_output(['git','show',commit+':'+p['path']],cwd=repo)).hexdigest()==p['sha256']
else:
 def fixture(path):
  data=subprocess.check_output(['git','show',commit+':'+path],cwd=repo);url=f'https://raw.githubusercontent.com/qoretechnologies/module-grpc/{commit}/{path}'
  with urllib.request.urlopen(url,timeout=90) as response:assert response.read()==data,url
  return {'path':path,'url':url,'sha256':hashlib.sha256(data).hexdigest()}
 with ThreadPoolExecutor(max_workers=6) as pool:fixtures=list(pool.map(fixture,sorted(mod.MODULE_FIXTURES['grpc'])))
 fixture_file.write_text(json.dumps(fixtures,indent=2)+'\n')
def prepare(target):
 repository={'fedora':'Fedora_44','el10':'AlmaLinux_10','leap':'openSUSE_Leap_16.0'}[target];folder=out/target;folder.mkdir()
 manifest=json.loads((root/f'qualification/databases-{target}-aarch64.json').read_text());manifest['packages']=[p for p in manifest['packages'] if not p['name'].startswith(('qore-freetds-module','qore-mysql-module'))];manifest['modules']=[{'name':'grpc','commit':commit,'fixtures':fixtures}]
 provenance={}
 def add(package,names,expected_source=None):
  base=f'/build/{project}/{repository}/aarch64/{package}';info=subprocess.check_output([*osc,base+'/_buildinfo']);(folder/(package+'-buildinfo.xml')).write_bytes(info);b=ET.fromstring(info)
  if expected_source:assert b.findtext('srcmd5')==expected_source,(package,b.findtext('srcmd5'))
  state=subprocess.check_output([*osc,f'/build/{project}/_result?package={package}&repository={repository}&arch=aarch64']);(folder/(package+'-result.xml')).write_bytes(state);s=ET.fromstring(state).find('result/status');assert s is not None and s.get('code')=='succeeded',(package,state)
  listing=subprocess.check_output([*osc,base]);(folder/(package+'-binaries.xml')).write_bytes(listing);files=[x.get('filename') for x in ET.fromstring(listing).findall('binary')]
  provenance[package]={'srcmd5':b.findtext('srcmd5'),'revision':b.findtext('rev')}
  for name in names:
   matches=[f for f in files if re.fullmatch(re.escape(name)+r'-[0-9].*\.(aarch64|noarch)\.rpm',f)];assert len(matches)==1,(name,matches)
   filename=matches[0];url='https://api.opensuse.org/public'+base+'/'+filename
   with urllib.request.urlopen(url,timeout=120) as response:data=response.read()
   (folder/filename).write_bytes(data);manifest['packages'].append({'name':name,'filename':filename,'url':url,'sha256':hashlib.sha256(data).hexdigest(),'phase':'runtime'})
 add('qore-grpc-module',['qore-grpc-module','qore-grpc-module-doc'],expected)
 add('qore-process-module',['qore-process-module'])
 if target=='leap':
  add('apache-arrow',['libarrow-acero2500','libarrow-compute2500','libarrow-dataset2500','libarrow-flight2500'],'a49cc7b1c2157efd3d77996e31d6bd14')
  add('python-pyarrow',['python313-pyarrow'],'01a5a921daefbd1d6a8c88a711b6f098')
  add('python-grpcio',['python313-grpcio'],'8503d6ee9a333c1e6b21b4164f49eab4')
  add('python-grpcio-tools',['python313-grpcio-tools'],'c720178b95adbbf36116b28fcb65a7a4')
 def verify(entry):
  p=folder/entry['filename']
  previous=root/'results/grpc-arm-inputs-20261008'/target/entry['filename']
  if not p.exists() and previous.is_file() and hashlib.sha256(previous.read_bytes()).hexdigest()==entry['sha256']:
   p.hardlink_to(previous)
  if not p.exists():
   with urllib.request.urlopen(entry['url'],timeout=120) as response:p.write_bytes(response.read())
  assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],entry['name']
 with ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(verify,manifest['packages']))
 mod.validate(manifest);path=root/f'qualification/grpc-{target}-aarch64.json';path.write_text(json.dumps(manifest,indent=2)+'\n');(folder/'sources.json').write_text(json.dumps(provenance,indent=2)+'\n');return target,len(manifest['packages'])
with ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(prepare,args.targets))
print('Verified manifest inputs:',results,flush=True)
