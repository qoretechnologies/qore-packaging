# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import ast,hashlib,importlib.util,json,os,subprocess,tarfile
root=Path.cwd();out=root/'results/leap-v8-node-canonical-final-installed-20261007';out.mkdir()
build=root/'results/leap-nodejs24-canonical-final-20261007';manifest=json.loads((build/'build.json').read_text());assert manifest['exit_code']==0
fixture=root/'work/leap-v8-node-canonical-final-installed-20261007';fixture.mkdir()
with tarfile.open(root/'work/v8-source-final-1/qore-v8-module-2.1.0.tar.xz') as tar:
 tar.extractall(fixture,filter='data')
fixture=fixture/'qore-v8-module-2.1.0'
script_ast=ast.parse((root/'work/qualify-leap-v8-node4-artifacts-1.py').read_text())
env=next(n.value.value for n in ast.walk(script_ast) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str) and any(isinstance(t,ast.Name) and t.id=='env' for t in n.targets))
record={'node_build':manifest,'steps':[]}
def save():(out/'status.json').write_text(json.dumps(record,indent=2)+'\n')
def run(name,cmd):
 with (out/(name+'.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=1800)
 record['steps'].append({'name':name,'exit_code':r.returncode,'command':cmd});save();r.check_returncode()
packages=[]
for rel,digest in manifest['artifacts'].items():
 assert hashlib.sha256((build/rel).read_bytes()).hexdigest()==digest
 if '/RPMS/' in rel:packages.append(rel)
for mode in ['sdk','runtime']:
 selected=packages if mode=='sdk' else [p for p in packages if Path(p).name.startswith('libnode137-24.')]
 name='qore-rpm-leap-v8-node-canonical-final-installed-'+mode+'-1'
 run(mode+'-install',['docker','run','--init','--name',name,'--network','none','-v',str(build)+':/rpms:ro','qore-rpm-keep:leap-v8-node4-final-1-'+mode,'rpm','-Uvh','--replacepkgs','--includedocs',*['/rpms/'+p for p in selected]])
 image=subprocess.check_output(['docker','commit',name,'qore-rpm-keep:leap-v8-node-canonical-final-installed-'+mode+'-1'],text=True).strip();record[mode+'_image']=image;save()
 subprocess.run(['docker','rm',name],check=True,stdout=subprocess.DEVNULL)
loader=importlib.util.spec_from_file_location('builder',root/'tools/build-local.py');builder=importlib.util.module_from_spec(loader);loader.loader.exec_module(builder)
with builder.build_network('docker',True) as (network,info):
 record['network']=info
 def command(mode,body):
  return ['docker','run','--rm','--init','--network',network,'--user','1019:100','-e','AUTOPKGTEST_TMP=/fixture','-v',str(fixture)+':/fixture','-w','/fixture',record[mode+'_image'],'sh','-c',env+body]
 run('sdk-consumer',command('sdk','rpm -V libnode137 libnode-devel qore-v8-module\nsh debian/tests/compiler\n'))
 run('runtime-tests',command('runtime','''for p in qore-devel gcc gcc-c++ libnode-devel; do if rpm -q "$p"; then exit 1; fi; done
rpm -V libnode137 qore-v8-module qore-v8-module-doc
./v8-smoke
sh debian/tests/cli
for suite in test/*.qtest; do
 timeout 600 qore -b --enable-debug -l v8 \
 -l /usr/lib64/qore-modules/TypeScriptProxy/TypeScriptProxy.qmod \
 -l /usr/lib64/qore-modules/TypeScriptActionInterface/TypeScriptActionInterface.qmod "$suite" -v
done
'''))
record['exit_code']=0;save()
