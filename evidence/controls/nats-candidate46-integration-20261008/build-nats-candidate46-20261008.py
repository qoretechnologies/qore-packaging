# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import re
import subprocess

root = Path.cwd()
verified = json.loads((root / 'results/nats-candidate46-patch-verification-20261008.json').read_text())
assert verified['patches'] == 109 and verified['fuzz'] == 0
assert verified['exact_focused_source_identity']
assert verified['changed_go_files_from_candidate45'] == ['server/jetstream_cluster_2_test.go']
for filename, count in [('nats-candidate46-tools-tests-20261008.log', 218),
                        ('nats-candidate46-runner-tests-20261008.log', 7)]:
    text = (root / 'results' / filename).read_text()
    assert re.search(r'Ran ' + str(count) + r' tests in [\d.]+s\n\nOK\s*$', text)
images = {
    'fedora': 'sha256:f1f889474f303ffe6f98b381e3061e812daa34e9018a00c4a25cb65f9a82fee9',
    'leap': 'sha256:2b44d9f9636b4e454c93b06c95cd9ff9f23136b159e80ac2ded68b32d7f1190b',
    'el10': 'sha256:0bc68ce99e4cd1340c79149a0601d7496351acd655a537ddae23116f036370c5'
}


def build(target):
    command = ['python3', '-B', '-W', 'error', 'tools/build-local.py', '--source',
               'work/nats-server-candidate-46', '--image', images[target], '--output',
               f'results/{target}-nats-server-candidate-46', '--jobs', '2',
               '--internal-interface', '--tmpfs-mib', '4096']
    with (root / f'results/{target}-nats-candidate46-driver-20261008.log').open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    return target, result.returncode


with ThreadPoolExecutor(max_workers=3) as pool:
    results = dict(pool.map(build, images))
(root / 'results/nats-candidate46-build-status-20261008.json').write_text(json.dumps(results, indent=2) + '\n')
print(results)
raise SystemExit(any(results.values()))
