# Copyright 2026 Qore Technologies, s.r.o.
from pathlib import Path
import concurrent.futures,json,os,subprocess
root=Path.cwd()
script='''set -eu
python3 -B -W error - <<'CHECK'
import importlib.util,pathlib,subprocess,json,hashlib
spec=importlib.util.spec_from_file_location('aot','/aot.py');aot=importlib.util.module_from_spec(spec);spec.loader.exec_module(aot)
mods=sorted(pathlib.Path('/usr/lib64/qore-modules').glob('*/*.qmod'))
owned=set(subprocess.check_output(['rpm','-ql','qore-jni-module'],text=True).splitlines())
mods=[p for p in mods if str(p) in owned]
assert sorted(p.parent.name for p in mods)==['AccessDataProvider', 'AvroDataProvider', 'BusyLightDataProvider', 'CamelDataProvider', 'EmailDataProvider', 'ExcelDataProvider', 'FlywayDataProvider', 'IcsDataProvider', 'JakartaJmsDataProvider', 'JasperReportsDataProvider', 'JdbcDataProvider', 'KafkaDataProvider', 'MqttDataProvider', 'OdpDataProvider', 'OdsDataProvider', 'OdtDataProvider', 'OpcUaDataProvider', 'PowerPointDataProvider', 'TikaDataProvider', 'VcfDataProvider', 'VisioDataProvider', 'WordDataProvider'],mods
for p in mods:
 trailers=aot.read_trailers(p);assert b'QAMD' in trailers,(p,'missing metadata trailer')
 sections=subprocess.check_output(['readelf','-S',str(p)],text=True)
 assert '.gnu_debuglink' in sections and '.debug_info' not in sections,p
 print(p.parent.name,'AOT metadata and separate debug link verified')
root=pathlib.Path('/work/payload');root.mkdir()
packages=list(pathlib.Path('/rpms/rpmbuild/RPMS').rglob('*-debug*.rpm'));assert len(packages)==2
for p in packages:
 payload=subprocess.check_output(['rpm2cpio',str(p)])
 subprocess.run(['cpio','-idm','--quiet'],input=payload,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True)
for p in mods:
 name=p.parent.name
 assert list(root.glob('usr/src/debug/**/'+name+'.qm')),name
 debug=list(root.glob('usr/lib/debug/**/'+name+'.qmod*.debug'));assert len(debug)==1,(name,debug)
 assert '.debug_info' in subprocess.check_output(['readelf','-S',str(debug[0])],text=True),name
notices=list(pathlib.Path('/usr/share/doc').glob('**/qore-jni-module/third-party-notices/provenance.json'));assert len(notices)==1
manifest=json.loads(notices[0].read_text())
count=0
jar_inodes={}
for name,d in manifest['dependencies'].items():
 notice=notices[0].parent/(name+'.txt');assert notice.is_file() and len(notice.read_text())>100,name
 assert b"\\r" not in notice.read_bytes(),notice
 for rel in d['paths']:
  if not rel.startswith('qlib/'):continue
  jar=pathlib.Path('/usr/share/qore-modules')/rel.removeprefix('qlib/')
  assert jar.is_file(),jar
  assert hashlib.sha256(jar.read_bytes()).hexdigest()==d['sha256'],jar
  jar_inodes.setdefault(d['sha256'],set()).add((jar.stat().st_dev,jar.stat().st_ino))
  count+=1
assert all(len(inodes)==1 for inodes in jar_inodes.values()),jar_inodes
print('Verified',count,'installed third-party JAR copies and',len(manifest['dependencies']),'notice/provenance records')
kt=list(pathlib.Path('/usr/share/doc').glob('**/qore-jni-kotlin/upstream-licenses'));assert len(kt)==1
original=pathlib.Path('/usr/share/qore/java/kotlin/license')
for p in original.rglob('*'):
 if p.is_file():assert (kt[0]/p.relative_to(original)).read_bytes()==p.read_bytes(),p
print('Kotlin upstream notices preserved verbatim')

for relative,interpreter in {**{name:'qore' for name in ('qjavac','qjava2jar','qjava-migrate-imports','qkotlinc')},**{'../share/qore/java/kotlin/bin/'+name:'bash' for name in ('kapt','kotlin','kotlinc','kotlinc-js','kotlinc-jvm')}}.items():
 p=pathlib.Path('/usr/bin')/relative
 assert p.read_bytes().splitlines()[0]==('#!/usr/bin/'+interpreter).encode(),p
 assert p.stat().st_mode&0o111,p
print('Nine installed launchers use their absolute distribution interpreters')
roots=list(pathlib.Path('/rpms/rpmbuild/BUILD').glob('qore-jni-module-*/build/vendor-kotlin/kotlinc/lib'))+list(pathlib.Path('/rpms/rpmbuild/BUILD').glob('*-build/qore-jni-module-*/build/vendor-kotlin/kotlinc/lib'))
assert len(roots)==1,roots
kotlin_inodes={}
for p in roots[0].glob('*.jar'):
 installed=pathlib.Path('/usr/share/qore/java/kotlin/lib')/p.name
 expected=hashlib.sha256(p.read_bytes()).hexdigest()
 assert hashlib.sha256(installed.read_bytes()).hexdigest()==expected,p
 kotlin_inodes.setdefault(expected,set()).add((installed.stat().st_dev,installed.stat().st_ino))
assert len(kotlin_inodes)>40 and all(len(inodes)==1 for inodes in kotlin_inodes.values())
print('Kotlin JAR bytes unchanged; identical payloads share inodes within their package')

CHECK
'''
def run(target):
 out=root/f'results/{target}-jni-metadata-candidate-artifacts-20261007';out.mkdir()
 work=root/f'work/{target}-jni-metadata-candidate-artifacts-20261007';work.mkdir()
 info=json.loads((root/f'results/{target}-jni-metadata-candidate-installed-2-20261007/status.json').read_text());assert info['exit_code']==0
 cmd=['docker','run','--rm','--init','--network','none','--user',f'{os.getuid()}:{os.getgid()}','-v',str(work)+':/work','-v',str(root/f'results/{target}-jni-rpm-metadata-candidate-20261007')+':/rpms:ro','-v',str(root.parent/'qore/rpm/preserve-aot-metadata.py')+':/aot.py:ro','-w','/work',info['sdk_image'],'sh','-c',script]
 with (out/'check.log').open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=600)
 (out/'status.json').write_text(json.dumps({'command':cmd,'exit_code':r.returncode},indent=2)+'\n');r.check_returncode()
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,['fedora','leap','el10']))
