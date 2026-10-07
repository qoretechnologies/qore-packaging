# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,importlib.util,json,subprocess,sys
root=Path.cwd();out=root/'work/python-native-command-integration2-20261007';out.mkdir()
sys.path.insert(0,str(root/'tools'));spec=importlib.util.spec_from_file_location('q',root/'tools/qualify-installed.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
names=['python'];catalog=json.loads((root/'catalog.json').read_text())['packages'];builds={'python':'results/fedora-python-final-1'};rpms=[];commands=[]
for name in names:
 d=json.loads((root/builds[name]/'build.json').read_text());assert d['exit_code']==0
 assert d['source']['commit']==catalog['module-'+name]['commit']
 rpm,=[k for k in d['artifacts'] if '/RPMS/x86_64/' in k and '-debug' not in k and '-doc-' not in k];path=root/builds[name]/rpm;assert hashlib.sha256(path.read_bytes()).hexdigest()==d['artifacts'][rpm];rpms.append('/results/'+str(path.relative_to(root/'results')))
 for phase in ['runtime','sdk']:
  directory=out/(phase+'-'+name);directory.mkdir()
  for p in sorted(q.MODULE_FIXTURES[name]):
   dest=directory/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(subprocess.check_output(['git','-C',str(root.parent/('module-'+name)),'show',catalog['module-'+name]['commit']+':'+p]));dest.chmod(0o755 if p.endswith(('.qtest','.py')) or p=='debian/tests/compiler' or p.startswith('rpm/tests-installed') else 0o644)
  container=Path('/work')/directory.name
  files=subprocess.check_output(['rpm','-qlp',str(path)],text=True)
  for suite,command in q.module_commands(name,phase,container,installed_files=files):commands.append({'name':phase+'-'+name+'-'+suite,'cwd':str(container),'command':command})
xml_build=root/'results/fedora-xml-final-build-2'
xml=json.loads((xml_build/'build.json').read_text());assert xml['exit_code']==0
assert xml['source']['commit']==catalog['module-xml']['commit']
xml_path,=[p for p in xml['artifacts'] if '/RPMS/x86_64/' in p and Path(p).name.startswith('qore-xml-module-') and '-debug' not in p]
assert hashlib.sha256((xml_build/xml_path).read_bytes()).hexdigest()==xml['artifacts'][xml_path]
rpms.append('/results/'+str((xml_build/xml_path).relative_to(root/'results')))
(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
(out/'run.py').write_text('''import json,os,subprocess\nfrom pathlib import Path\nresults=[]\nfor entry in json.loads(Path('/work/commands.json').read_text()):\n env={**os.environ,'AUTOPKGTEST_TMP':entry['cwd']}\n print(entry['name'],flush=True)\n process=subprocess.run(entry['command'],cwd=entry['cwd'],env=env)\n results.append({**entry,'exit_code':process.returncode})\n if process.returncode:break\nPath('/work/result.json').write_text(json.dumps(results,indent=2)+'\\n')\nassert all(r['exit_code']==0 for r in results)\n''')
command=['docker','run','--rm','--init','--network','none','-v',str(root/'results')+':/results:ro','-v',str(out)+':/work',subprocess.check_output(['docker','image','inspect','--format','{{.Id}}','qore-rpm-keep:fedora-zmq-sdk21-20261006'],text=True).strip(),'sh','-eu','-c','rpm -U --replacepkgs "$@"\nexec setpriv --reuid=1019 --regid=100 --clear-groups --reset-env python3 -B -W error /work/run.py','install',*rpms]
(out/'command.json').write_text(json.dumps(command,indent=2)+'\n')
with (root/'results/python-native-command-integration2-20261007.log').open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
(out/'status.json').write_text(json.dumps({'exit_code':r.returncode},indent=2)+'\n');sys.exit(r.returncode)
