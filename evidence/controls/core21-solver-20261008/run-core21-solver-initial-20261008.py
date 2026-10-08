# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import subprocess

root = Path(__file__).resolve().parent.parent
out = root / 'results/core21-solver-20261008'
out.mkdir()
prepared = json.loads((root / 'results/core21-solver-repositories-20261008/status.json').read_text())
assert len(prepared['targets']) == 6 and not prepared['private_key_retained']


def check(pair):
    target, definition = pair
    image = json.loads((root / 'targets' / (definition + '.json')).read_text())['image']
    directory = out / target
    directory.mkdir()
    bootstrap = ('zypper --non-interactive install --no-recommends python3 ca-certificates shadow util-linux findutils'
        if target == 'leap' else
        'dnf -y --setopt=install_weak_deps=False install python3 ca-certificates shadow-utils util-linux findutils'
        + (' dnf-plugins-core epel-release\ndnf config-manager --set-enabled crb' if target == 'el10' else ''))
    command = ['docker', 'run', '--rm', '--init', '--name', 'qore-core21-solver-' + target + '-20261008',
        '-v', str(root / 'work/check-core21-solver-20261008.py') + ':/check.py:ro',
        '-v', str(root / 'tools') + ':/tools:ro',
        '-v', str(root / 'qualification/jni-fixtures.json') + ':/qualification/jni-fixtures.json:ro',
        '-v', str(root / 'work/core21-solver-repositories-20261008' / (target + '-x86_64')) + ':/repository:ro',
        '-v', str(root / 'work/core21-upgrade-baseline-20261008' / (target + '-x86_64') / 'fixtures') + ':/fixtures:ro',
        '-v', str(root / 'results/core21-solver-repositories-20261008/status.json') + ':/repository-status.json:ro',
        '-v', str(root / 'results/core21-upgrade-baseline-20261008' / (target + '-x86_64') / 'manifest.json') + ':/manifest.json:ro',
        '-v', str(directory) + ':/results', image, 'sh', '-c',
        'set -eu\n' + bootstrap + '\nexec python3 -B -W error /check.py']
    with (directory / 'driver.log').open('x') as log:
        process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    result = {'image': image, 'exit_code': process.returncode, 'command': command}
    (directory / 'driver.json').write_text(json.dumps(result, indent=2) + '\n')
    return target, result


with ThreadPoolExecutor(max_workers=3) as pool:
    results = dict(pool.map(check, [('fedora', 'fedora-44'), ('leap', 'leap-16.0'), ('el10', 'el-10')]))
(out / 'status.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps({k: v['exit_code'] for k, v in results.items()}))
raise SystemExit(any(v['exit_code'] for v in results.values()))
