# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import tarfile

root = Path.cwd()
names = ['nats-publication-231-20261007', 'nats-purge-route-232-20261007',
         'nats-peer-236-20261007', 'nats-purge-237-20261007', 'nats-snapshot-240-20261007']
qualified = {}
for name in names:
    record = json.loads((root / 'evidence' / (name + '.json')).read_text())
    for relative, digest in record['files_sha256'].items():
        path = root / relative
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, relative
        if path.name.endswith('.patch'):
            installed = root / 'dependencies' / path.name
            assert installed.read_bytes() == path.read_bytes(), path.name
            qualified[path.name] = {'sha256': digest, 'evidence': 'evidence/' + name + '.json'}
assert len(qualified) == 5
patches = re.findall(r'^Patch\d+: (\S+)$', (root / 'dependencies/nats-server.spec').read_text(), re.M)
assert len(patches) == 108 and set(patches[-5:]) == set(qualified)
bundle = root / 'work/nats-server-candidate-45'
out = root / 'work/nats-prepared-45'
source = out / 'nats-server-2.15.0'
if not sys.argv[1:]:
    with (root / 'results/nats-candidate45-prepare.log').open('x') as log:
        subprocess.run(['python3', '-B', '-W', 'error', 'tools/prepare-dependency.py', '--name', 'nats-server',
                        '--candidate', '--cache', 'work/nats-server-candidate-44',
                        '--output', 'work/nats-server-candidate-45'], check=True, stdout=log)
    out.mkdir()
    with tarfile.open(bundle / 'nats-server-2.15.0.tar.gz') as archive:
        archive.extractall(out, filter='data')
    with tarfile.open(bundle / 'nats-server-2.15.0-vendor.tar.xz') as archive:
        archive.extractall(source, filter='data')
    with (root / 'results/nats-candidate45-patches.log').open('x') as log:
        for patch in patches:
            result = subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(bundle / patch)],
                                    cwd=source, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            log.write(result.stdout)
            assert result.returncode == 0 and 'fuzz' not in result.stdout.lower(), (patch, result.stdout)
else:
    assert sys.argv[1:] == ['--verify-prepared']
    log = (root / 'results/nats-candidate45-patches.log').read_text()
    assert 'FAILED' not in log and 'fuzz' not in log.lower()
    manifest = json.loads((bundle / 'source-manifest.json').read_text())
    for name, digest in manifest['sources'].items():
        assert hashlib.sha256((bundle / name).read_bytes()).hexdigest() == digest, name
        current = root / 'dependencies' / name
        if current.is_file():
            assert current.read_bytes() == (bundle / name).read_bytes(), name
previous = root / 'work/nats-prepared-44/nats-server-2.15.0'
expected = set()
for name in qualified:
    expected.update(re.findall(r'^\+\+\+ b/(\S+)$', (bundle / name).read_text(), re.M))
changed = []
for path in source.rglob('*.go'):
    if not path.is_file():
        continue
    relative = str(path.relative_to(source))
    if path.read_bytes() != (previous / relative).read_bytes():
        changed.append(relative)
assert set(changed) == expected
record = {'patches': 108, 'fuzz': 0, 'changed_from_candidate44': sorted(changed),
          'focused_qualified_patch_identity': qualified,
          'source_manifest': json.loads((bundle / 'source-manifest.json').read_text()),
          'remaining': 'ConsumerInfo restart timeout and historical full-suite gates remain unresolved; this matrix qualifies accumulated focused corrections and may reproduce the remaining failures.'}
(root / 'results/nats-candidate45-patch-verification.json').write_text(json.dumps(record, indent=2) + '\n')
print('Verified all 108 patches; only the seven focused-qualified test files differ from candidate44')
