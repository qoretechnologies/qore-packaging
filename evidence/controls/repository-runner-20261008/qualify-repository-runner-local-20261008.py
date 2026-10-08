# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Exercise the reusable repository mode on fresh native x86_64 containers."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import subprocess

root = Path(__file__).resolve().parent.parent
out = root / 'results/repository-runner-local-20261008'
out.mkdir()
paths = ['tools/qualify-installed.py', 'tools/repository_fixture.py', 'tests/test_repository_fixture.py']
pins = {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths}
(out / 'source.json').write_text(json.dumps(pins, indent=2) + '\n')


def qualify(pair):
    target, definition = pair
    image = json.loads((root / 'targets' / (definition + '.json')).read_text())['image']
    directory = out / target
    directory.mkdir()
    bootstrap = ('zypper --non-interactive install --no-recommends python3 ca-certificates shadow util-linux findutils createrepo_c gpg2'
        if target == 'leap' else
        'dnf -y --setopt=install_weak_deps=False install python3 ca-certificates shadow-utils util-linux findutils createrepo_c gnupg2'
        + (' dnf-plugins-core epel-release\ndnf config-manager --set-enabled crb' if target == 'el10' else ''))
    command = ['docker', 'run', '--rm', '--init', '--pull=never', '--name', 'qore-repository-runner-' + target + '-20261008',
        '-v', str(root / 'tools') + ':/tools:ro',
        '-v', str(root / 'qualification/jni-fixtures.json') + ':/qualification/jni-fixtures.json:ro',
        '-v', str(root / 'results/core21-upgrade-baseline-20261008' / (target + '-x86_64') / 'manifest.json') + ':/manifest.json:ro',
        '-v', str(directory) + ':/results', image, 'sh', '-c',
        'set -eu\n' + bootstrap + '\nexec python3 -B -W error /tools/qualify-installed.py /manifest.json --repository-install --output /results/qualification']
    with (directory / 'driver.log').open('x') as log:
        process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    result = {'image': image, 'exit_code': process.returncode, 'command': command}
    (directory / 'driver.json').write_text(json.dumps(result, indent=2) + '\n')
    print(target, process.returncode, flush=True)
    return target, result


with ThreadPoolExecutor(max_workers=3) as pool:
    results = dict(pool.map(qualify, [('fedora', 'fedora-44'), ('leap', 'leap-16.0'), ('el10', 'el-10')]))
(out / 'status.json').write_text(json.dumps(results, indent=2) + '\n')
assert pins == {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths}
raise SystemExit(any(v['exit_code'] for v in results.values()))
