# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

root = Path.cwd()
sys.path.insert(0, str(root / 'tools'))
spec = importlib.util.spec_from_file_location('installed', root / 'tools/qualify-installed.py')
installed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installed)
out = root / 'results/database-installed-commands-20261008'
out.mkdir()
fixtures = root / 'work/database-installed-fixtures-20261008'
fixtures.mkdir()
commits = {'freetds': '2b35358523ff5f397e415203e0df37d38825e8eb', 'mysql': 'c7ba6b020d76a463d047608eafee5218da0f3c97'}
source_hashes = {}
for name, commit in commits.items():
    repo = root.parent / ('module-' + installed.MODULE_REPOSITORIES.get(name, name))
    for relative in installed.MODULE_FIXTURES[name]:
        data = subprocess.check_output(['git', 'show', commit + ':' + relative], cwd=repo)
        path = fixtures / name / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o755 if path.suffix in ('.py', '.qtest') or relative == 'debian/tests/compiler' else 0o644)
        source_hashes[name + '/' + relative] = hashlib.sha256(data).hexdigest()
(out / 'fixture-hashes.json').write_text(json.dumps(source_hashes, indent=2) + '\n')
freetds = json.loads((root / 'evidence/freetds-rpm-final-20261002.json').read_text())['targets']
mysql = json.loads((root / 'evidence/xmlsec-and-obs-fixes-20261002.json').read_text())['qualification']
cases = []
for target in ['fedora', 'leap', 'el10']:
    for name in commits:
        prior = freetds[target]['installed'] if name == 'freetds' else mysql[target]['mysql']
        assert prior['exit_code'] == 0
        for phase in ['runtime', 'sdk']:
            image = prior[phase + '_image']
            subprocess.run(['docker', 'image', 'inspect', image], stdout=subprocess.DEVNULL, check=True)
            cases.append((target, name, phase, image))

def run(case):
    target, name, phase, image = case
    steps = []
    for label, command in installed.module_commands(name, phase, Path('/fixtures')):
        full = ['docker', 'run', '--rm', '--init', '--network', 'none', '--user', str(os.getuid()) + ':' + str(os.getgid()),
                '-v', str(fixtures / name) + ':/fixtures:ro', image, *command]
        log_path = out / (target + '-' + name + '-' + phase + '-' + label + '.log')
        with log_path.open('x') as log:
            result = subprocess.run(full, stdout=log, stderr=subprocess.STDOUT)
        steps.append({'name': label, 'command': full, 'exit_code': result.returncode})
        if result.returncode:
            break
    result = {'target': target, 'module': name, 'phase': phase, 'image': image, 'steps': steps}
    (out / (target + '-' + name + '-' + phase + '.json')).write_text(json.dumps(result, indent=2) + '\n')
    print(target, name, phase, [s['exit_code'] for s in steps], flush=True)
    return result

with ThreadPoolExecutor(max_workers=4) as pool:
    results = list(pool.map(run, cases))
(out / 'status.json').write_text(json.dumps(results, indent=2) + '\n')
raise SystemExit(any(step['exit_code'] for row in results for step in row['steps']))
