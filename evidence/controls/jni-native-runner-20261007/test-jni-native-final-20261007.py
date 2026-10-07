# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import concurrent.futures
import hashlib
import json
import shutil
import subprocess
import sys

root = Path.cwd()
code = root / 'work/jni-native-final-code-20261007'
code.mkdir(exist_ok=True)
inputs = ['tools/qualify-installed.py', 'tools/installed_jni.py', 'tools/packaging.py',
          'qualification/jni-fixtures.json']
inputs += ['work/jni-' + target + '-x86_64.json' for target in ('fedora', 'leap', 'el10')]
hashes = {}
for name in inputs:
    target = code / name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == (root / name).read_bytes(), name
    else:
        shutil.copy2(root / name, target)
    hashes[name] = hashlib.sha256(target.read_bytes()).hexdigest()
(code / 'inputs.json').write_text(json.dumps(hashes, indent=2) + '\n')

def run(target):
    prior = root / ('results/' + target + '-jni-native-clean-20261007' + ('' if target == 'el10' else '-2'))
    image = json.loads((prior / 'status.json').read_text())['bootstrap_image']
    subprocess.run(['docker', 'image', 'inspect', image], check=True, stdout=subprocess.DEVNULL)
    output = root / ('results/' + target + '-jni-native-final-20261007')
    output.mkdir()
    record = {'bootstrap_image': image, 'code_sha256': hashes, 'steps': []}
    try:
        for phase in ('sdk', 'runtime'):
            command = ['docker', 'run', '--rm', '--init', '-v', str(code) + ':/code:ro',
                       '-v', str(output) + ':/output', '-w', '/code', image,
                       'python3', '-B', '-W', 'error', 'tools/qualify-installed.py',
                       'work/jni-' + target + '-x86_64.json', '--output', '/output/' + phase,
                       '--jni-phase', phase, '--jni-fixtures', '/output/jni-fixtures']
            with (output / (phase + '.log')).open('w') as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=7200)
            record['steps'].append({'name': phase, 'command': command, 'exit_code': result.returncode})
            result.check_returncode()
        record['exit_code'] = 0
    except BaseException as error:
        record.update(exit_code=1, error=repr(error))
        raise
    finally:
        (output / 'status.json').write_text(json.dumps(record, indent=2) + '\n')
    return target

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    print(list(pool.map(run, sys.argv[1:] or ('fedora', 'leap', 'el10'))))
