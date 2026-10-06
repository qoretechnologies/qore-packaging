# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,importlib.util,json,subprocess,sys
root=Path.cwd();out=root/'work/ssh2-proj-installed-commands-20261006';out.mkdir();sys.path.insert(0,str(root/'tools'));s=importlib.util.spec_from_file_location('q',root/'tools/qualify-installed.py');q=importlib.util.module_from_spec(s);s.loader.exec_module(q)
(out/'run.py').write_text('''# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,os,subprocess
out=Path('/work');results=[]
for entry in json.loads((out/'commands.json').read_text()):
 env=os.environ.copy()
 for key in ('QORE_MODULE_DIR','QORE_MODULE_DIR_ONLY','QORE_INCLUDE_DIR','LD_LIBRARY_PATH','LD_PRELOAD'):env.pop(key,None)
 env['AUTOPKGTEST_TMP']=entry['cwd']
 with (out/(entry['name']+'.log')).open('x') as log:r=subprocess.run(entry['command'],cwd=entry['cwd'],env=env,stdout=log,stderr=subprocess.STDOUT)
 results.append({**entry,'exit_code':r.returncode});(out/'checks.json').write_text(json.dumps(results,indent=2)+'\\n');r.check_returncode()
''')
def run(case):
 mod,target=case;directory=out/(mod+'-'+target);directory.mkdir();commands=[];repo=root/f'work/checkouts/module-{mod}-metadata-20261006'
 build=root/f'results/{target}-{mod}-metadata-final-20261006';b=json.loads((build/'build.json').read_text());assert b['exit_code']==0 and not b['source'].get('candidate');commit=b['source']['commit']
 rpm,=[n for n in b['artifacts'] if '/RPMS/x86_64/' in n and '-debug' not in n and 'qore-'+mod+'-module-' in n];p=build/rpm;assert hashlib.sha256(p.read_bytes()).hexdigest()==b['artifacts'][rpm]
 installed_files=subprocess.check_output(['rpm','-qpl',str(p)],text=True)
 for phase in ('runtime','sdk'):
  fixture=directory/phase;fixture.mkdir()
  for rel in q.MODULE_FIXTURES[mod]:
   path=fixture/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(subprocess.check_output(['git','-C',str(repo),'show',commit+':'+rel]));path.chmod(0o755)
  for suite,command in q.module_commands(mod,phase,Path('/work')/phase,installed_files=installed_files,family={'fedora':'fedora','leap':'suse','el10':'el'}[target]):commands.append({'name':phase+'-'+suite,'command':command,'cwd':'/work/'+phase})
 (directory/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');images=json.loads((root/f'results/{mod}-sdk21-debugedit51-images-20261006.json').read_text())
 cmd=['docker','run','--rm','--init','--network','none','-v',str(directory)+':/work','-v',str(out/'run.py')+':/run.py:ro','-v',str(p)+':/module.rpm:ro',images[target],'sh','-eu','-c','rpm -U --replacepkgs /module.rpm\nexec setpriv --reuid=1019 --regid=100 --clear-groups --reset-env python3 -B -W error /run.py']
 with (directory/'run.log').open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 (directory/'status.json').write_text(json.dumps({'exit_code':r.returncode,'command':cmd,'source_commit':commit,'rpm_sha256':b['artifacts'][rpm]},indent=2)+'\n');return mod+'-'+target,r.returncode
with ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(run,[(mod,target) for mod in ('ssh2','proj') for target in ('fedora','leap','el10')]))
(out/'status.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
