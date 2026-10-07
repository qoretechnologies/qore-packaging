# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import re
import subprocess

root = Path.cwd()
verified = json.loads((root / 'results/nats-candidate45-patch-verification.json').read_text())
assert verified['patches'] == 108 and verified['fuzz'] == 0
assert len(verified['focused_qualified_patch_identity']) == 5
for filename, count in [('node-built-library-tools-tests-20261007.log', 214),
                        ('nats-candidate45-runner-tests-20261007.log', 7)]:
    text = (root / 'results' / filename).read_text()
    assert re.search(r'Ran ' + str(count) + r' tests in [\d.]+s\n\nOK\s*$', text)
images = {
    'fedora': 'sha256:f1f889474f303ffe6f98b381e3061e812daa34e9018a00c4a25cb65f9a82fee9',
    'leap': 'sha256:2b44d9f9636b4e454c93b06c95cd9ff9f23136b159e80ac2ded68b32d7f1190b',
    'el10': 'sha256:0bc68ce99e4cd1340c79149a0601d7496351acd655a537ddae23116f036370c5'
}


def build(target):
    command = ['python3', '-B', '-W', 'error', 'tools/build-local.py', '--source',
               'work/nats-server-candidate-45', '--image', images[target], '--output',
               f'results/{target}-nats-server-candidate-45', '--jobs', '2',
               '--internal-interface', '--tmpfs-mib', '4096']
    with (root / f'results/{target}-nats-candidate45-driver-20261007.log').open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    return target, result.returncode


with ThreadPoolExecutor(max_workers=3) as pool:
    results = dict(pool.map(build, images))
(root / 'results/nats-candidate45-build-status-20261007.json').write_text(json.dumps(results, indent=2) + '\n')
print(results)
raise SystemExit(any(results.values()))
