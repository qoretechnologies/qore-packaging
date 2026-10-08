# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib, importlib.util, json, shutil, subprocess, sys

root = Path.cwd()
checkout=root/'work/checkouts/packaging-xml-installed-20261008'
sys.path.insert(0, str(checkout / 'tools'))
loader = importlib.util.spec_from_file_location('installed', checkout / 'tools/qualify-installed.py')
module = importlib.util.module_from_spec(loader)
loader.loader.exec_module(module)
out = root / 'results/xml-installed-runner-20261008'
out.mkdir()
previous = json.loads((root / 'evidence/xml-canonical-20261002.json').read_text())['targets']
fixture_source=root/'work/xml-installed-archive-fixtures-20261008'
info=module.installed_xml.stage(fixture_source)
assert info=={'files':1721,'bytes':91940823,'suites':304}
(out/'archive-fixtures.json').write_text(json.dumps(info,indent=2)+'\n')
script = out / 'run.py'
script.write_text('''from pathlib import Path
import importlib.util,json,os,subprocess,sys
sys.path.insert(0,'/packaging/tools')
loader=importlib.util.spec_from_file_location('installed','/packaging/tools/qualify-installed.py')
module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)
phase=sys.argv[1];out=Path('/results');results=[]
if phase=='sdk':
 subprocess.run(['rpm','-U',sys.argv[2]],check=True)
 subprocess.run(['rpm','-V','qore-xml-module'],check=True)
 os.setgroups([]);os.setgid(100);os.setuid(1019)
os.environ['AUTOPKGTEST_TMP']='/fixture'
if phase=='runtime':
 for name in ('qore-devel','gcc','gcc-c++'):
  assert subprocess.run(['rpm','-q',name],stdout=subprocess.DEVNULL).returncode==1,name
for variable in ('QORE_MODULE_DIR','QORE_MODULE_DIR_ONLY','QORE_INCLUDE_DIR','LD_LIBRARY_PATH','LD_PRELOAD'):
 os.environ.pop(variable,None)
for name,command in module.module_commands('xml',phase,Path('/fixture')):
 with (out/(name+'.log')).open('w') as log:
  result=subprocess.run(command,cwd='/fixture',stdout=log,stderr=subprocess.STDOUT)
 results.append({'name':name,'command':command,'exit_code':result.returncode})
 (out/'status.json').write_text(json.dumps(results,indent=2)+'\\n')
 print(name,result.returncode,flush=True);result.check_returncode()
''')

def run(target):
    results = {}
    for phase in ('runtime', 'sdk'):
        output = out / target / phase
        output.mkdir(parents=True)
        fixture = root / f'work/xml-installed-runner-{target}-{phase}-20261008'
        shutil.copytree(fixture_source, fixture)
        original=json.loads((root/f'results/{target}-xml-ssh2-final-2.json').read_text())
        image=original['xml_runtime_image'] if phase=='runtime' else original['sdk_image']
        build=previous[target]['build']
        filename,= [p for p in build['artifacts'] if '/RPMS/' in p and Path(p).name.startswith('qore-xml-module-2.')]
        rpms=root/f'results/{target}-xml-final-build-2'
        with (rpms/filename).open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==build['artifacts'][filename]
        command = ['docker', 'run', '--rm', '--init', '--network', 'none', '--user', '1019:100' if phase=='runtime' else '0:0',
                   '-v', str(checkout) + ':/packaging:ro', '-v', str(fixture) + ':/fixture',
                   '-v', str(rpms)+':/rpms:ro', '-v', str(output) + ':/results', '-v', str(script) + ':/run.py:ro', '-w', '/fixture',
                   image, 'python3', '-B', '-W', 'error', '/run.py', phase, '/rpms/'+filename]
        with (output / 'driver.log').open('x') as log:
            process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        results[phase] = {'command': command, 'image': image, 'exit_code': process.returncode}
        (out / target / 'status.json').write_text(json.dumps(results, indent=2) + '\n')
        print(target, phase, process.returncode, flush=True)
        process.check_returncode()
    return target, 0

with ThreadPoolExecutor(max_workers=3) as pool:
    results = dict(pool.map(run, ['fedora', 'leap', 'el10']))
(out / 'status.json').write_text(json.dumps(results, indent=2) + '\n')
