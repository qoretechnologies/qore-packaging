# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import concurrent.futures
import json
import subprocess

root = Path.cwd()
output = root / 'results/core-index-recipe-2-20261007'
output.mkdir()


def run(target):
    build = root / f'results/{target}-core-sdk22-canonical-final-20261007'
    record = json.loads((build / 'build.json').read_text())
    sources = list((build / 'rpmbuild/BUILD').glob('qore-*/CMakeLists.txt'))
    sources += list((build / 'rpmbuild/BUILD').glob('qore-*/qore-*/CMakeLists.txt'))
    assert len(sources) == 1
    source = '/work/' + str(sources[0].parent.relative_to(build))
    script = r'''import hashlib,importlib.util,json,pathlib,re,shlex,shutil,subprocess,sys
source=pathlib.Path(sys.argv[1])
loader=importlib.util.spec_from_file_location('preserve',source/'rpm/preserve-aot-metadata.py')
helper=importlib.util.module_from_spec(loader);loader.loader.exec_module(helper)
parsed=subprocess.run(['rpmspec','-P','--define','_topdir /tmp/core-index-stage','--define','buildroot /tmp/core-index-stage/BUILDROOT','/control/qore.spec-multi'],capture_output=True,text=True,check=True)
assert not parsed.stderr,parsed.stderr
install=parsed.stdout.split('%install\n',1)[1].split('%check\n',1)[0]
match=re.search(r'(?m)^python3 rpm/preserve-aot-metadata\.py .*?-exec objcopy --remove-section=\.debug_names .*?\\;\n',install,re.S)
assert match,install
command=match[0];args=shlex.split(command.replace('\\\n',''))
destination=pathlib.Path(args[2]);assert destination.is_relative_to('/tmp'),destination
assert str(destination).endswith('/usr/lib64/qore-modules/3.0.0'),destination
destination.mkdir(parents=True)
saved={}
for name in ('QUnit','MapperUtil'):
 original=source/'build/qlib-qmod'/(name+'.qmod');fixed=destination/(name+'.qmod')
 shutil.copy2(original,fixed)
 saved[name]={'metadata':helper.read_trailers(original),'symbols':subprocess.check_output(['nm','-a',str(original)])}
outside=destination.parent/'outside-api-2.0.qmod';shutil.copy2(source/'build/qlib-qmod/QUnit.qmod',outside)
outside_hash=hashlib.sha256(outside.read_bytes()).hexdigest()
result=subprocess.run(['/bin/sh','-ec',command],cwd=source,capture_output=True,text=True,check=True)
assert not result.stdout and not result.stderr,(result.stdout,result.stderr)
for name,record in saved.items():
 fixed=destination/(name+'.qmod')
 assert '.debug_names' not in subprocess.check_output(['readelf','-SW',str(fixed)],text=True)
 assert helper.read_trailers(fixed)==record['metadata']
 assert subprocess.check_output(['nm','-a',str(fixed)])==record['symbols']
assert hashlib.sha256(outside.read_bytes()).hexdigest()==outside_hash
print('PASS: exact RPM install command preserves two real AOT modules and does not modify a module outside the standard-library tree')
print(command)
'''
    command = ['docker', 'run', '--rm', '--init', '--network', 'none',
               '-v', str(build) + ':/work:ro', '-v',
               str(root / 'work/core-aot-index-proposal-20261007/qore.spec-multi') + ':/control/qore.spec-multi:ro',
               record['image'], 'python3', '-B', '-W', 'error', '-c', script, source]
    with (output / (target + '.log')).open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    return {'target': target, 'command': command, 'exit_code': result.returncode}


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    records = list(pool.map(run, ('fedora', 'leap', 'el10')))
(output / 'status.json').write_text(json.dumps(records, indent=2) + '\n')
print({row['target']: row['exit_code'] for row in records})
assert all(row['exit_code'] == 0 for row in records)
