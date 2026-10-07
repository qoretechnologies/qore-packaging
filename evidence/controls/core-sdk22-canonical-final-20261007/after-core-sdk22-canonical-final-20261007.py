# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import concurrent.futures
import json
import os
import select
import subprocess

root = Path.cwd()
descriptors = []
for path in Path('/proc').iterdir():
    if not path.name.isdigit():
        continue
    try:
        command = (path / 'cmdline').read_bytes().split(b'\0')
        if b'work/build-core-sdk22-canonical-final-20261007.py' in command:
            descriptors.append(os.pidfd_open(int(path.name)))
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        continue
while descriptors:
    ready, _, _ = select.select(descriptors, [], [])
    for descriptor in ready:
        descriptors.remove(descriptor)
        os.close(descriptor)
for target in ('fedora', 'leap', 'el10'):
    path = root / ('results/' + target + '-core-sdk22-canonical-final-20261007')
    manifest = json.loads((path / 'build.json').read_text())
    assert manifest['exit_code'] == 0, target
    assert manifest['source']['commit'] == '49152d805b73c417db2bf3c0ac72dd22bfa8f058'
    assert 'Passed 400 out of 400 tests. 0 tests failed.' in (path / 'build.log').read_text(), target

def qualify(target):
    path = root / ('results/' + target + '-core-sdk22-canonical-installed-driver-20261007.log')
    with path.open('x') as log:
        result = subprocess.run(['python3', '-B', '-W', 'error',
                 'work/qualify-core-sdk22-canonical-final-20261007.py', target],
                 stdout=log, stderr=subprocess.STDOUT)
    return target, result.returncode

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    result = dict(pool.map(qualify, ('fedora', 'leap', 'el10')))
(root / 'results/core-sdk22-canonical-installed-matrix-20261007.json').write_text(json.dumps(result, indent=2) + '\n')
print(result, flush=True)
