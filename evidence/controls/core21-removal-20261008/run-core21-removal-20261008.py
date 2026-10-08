# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import subprocess

root = Path(__file__).resolve().parent.parent
out = root / 'results/core21-removal-final2-20261008'
out.mkdir()


def run(target):
    record = json.loads((root / f'results/{target}-core-policy-21-installed-3.json').read_text())
    assert record['exit_code'] == 0
    directory = out / target
    directory.mkdir()
    command = ['docker', 'run', '--rm', '--init', '--network', 'none',
               '--name', 'qore-core21-removal-' + target + '-20261008',
               '-v', str(root / 'work/check-core21-removal-20261008.py') + ':/check.py:ro',
               '-v', str(root / 'tools') + ':/tools:ro',
               '-v', str(root / 'qualification/jni-fixtures.json') + ':/qualification/jni-fixtures.json:ro',
               '-v', str(root / f'work/core21-upgrade-baseline-20261008/{target}-x86_64') + ':/baseline:ro',
               '-v', str(root / f'results/core21-upgrade-baseline-20261008/{target}-x86_64/manifest.json') + ':/manifest.json:ro',
               '-v', str(directory) + ':/results', record['sdk_image'], 'python3', '-B', '-W', 'error', '/check.py']
    with (directory / 'driver.log').open('x') as log:
        process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    value = {'exit_code': process.returncode, 'image': record['sdk_image'], 'command': command}
    (directory / 'driver.json').write_text(json.dumps(value, indent=2) + '\n')
    return target, value


with ThreadPoolExecutor(max_workers=3) as pool:
    results = dict(pool.map(run, ('fedora', 'leap', 'el10')))
(out / 'status.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps({k: v['exit_code'] for k, v in results.items()}))
raise SystemExit(any(v['exit_code'] for v in results.values()))
