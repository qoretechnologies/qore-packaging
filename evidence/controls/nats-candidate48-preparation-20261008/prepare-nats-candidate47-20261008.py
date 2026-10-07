# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tarfile

root = Path.cwd()
evidence = json.loads((root / 'evidence/nats-failtracking-meta-20261008.json').read_text())
for relative, digest in evidence['files_sha256'].items():
    assert hashlib.sha256((root / relative).read_bytes()).hexdigest() == digest, relative
name = 'nats-server-failtracking-meta-ready-tests.patch'
qualified = root / 'evidence/controls/nats-failtracking-meta-20261008' / name
assert (root / 'dependencies' / name).read_bytes() == qualified.read_bytes()
patches = re.findall(r'^Patch\d+: (\S+)$', (root / 'dependencies/nats-server.spec').read_text(), re.M)
assert len(patches) == 110 and patches[-1] == name
bundle = root / 'work/nats-server-candidate-47'
out = root / 'work/nats-prepared-47'
source = out / 'nats-server-2.15.0'
with (root / 'results/nats-candidate47-prepare-20261008.log').open('x') as log:
    subprocess.run(['python3', '-B', '-W', 'error', 'tools/prepare-dependency.py', '--name', 'nats-server',
                    '--candidate', '--cache', 'work/nats-server-candidate-46', '--output', str(bundle)],
                   check=True, stdout=log)
out.mkdir()
with tarfile.open(bundle / 'nats-server-2.15.0.tar.gz') as archive:
    archive.extractall(out, filter='data')
with tarfile.open(bundle / 'nats-server-2.15.0-vendor.tar.xz') as archive:
    archive.extractall(source, filter='data')
with (root / 'results/nats-candidate47-patches-20261008.log').open('x') as log:
    for patch in patches:
        result = subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(bundle / patch)],
                                cwd=source, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log.write(result.stdout)
        assert result.returncode == 0 and 'fuzz' not in result.stdout.lower(), (patch, result.stdout)
        if patch == name:
            assert 'offset' not in result.stdout.lower()
previous = root / 'work/nats-prepared-46/nats-server-2.15.0'
changes = []
for path in source.rglob('*.go'):
    if path.is_file():
        relative = str(path.relative_to(source))
        if path.read_bytes() != (previous / relative).read_bytes():
            changes.append(relative)
assert changes == ['server/jetstream_cluster_3_test.go'], changes
assert (source / changes[0]).read_bytes() == (root / 'work/nats-failtracking-clean-252-20261008/jetstream_cluster_3_test.go').read_bytes()
manifest = json.loads((bundle / 'source-manifest.json').read_text())
for relative, digest in manifest['sources'].items():
    assert hashlib.sha256((bundle / relative).read_bytes()).hexdigest() == digest, relative
old = json.loads((root / 'work/nats-server-candidate-46/source-manifest.json').read_text())
delta = [n for n, h in manifest['sources'].items() if h != old['sources'].get(n)]
assert sorted(delta) == sorted([name, 'nats-server.spec', 'nats-server.changes']), delta
record = {'schema': 1, 'patches': 110, 'fuzz': 0, 'new_patch_offsets': 0,
          'changed_go_files_from_candidate46': changes, 'changed_bundle_files': delta,
          'exact_focused_source_identity': True, 'qualification': 'evidence/nats-failtracking-meta-20261008.json',
          'source_manifest': manifest,
          'remaining': 'Full candidate RPM builds and separate historical performance, atomic-batch and workqueue gates remain required.'}
(root / 'results/nats-candidate47-patch-verification-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('All 110 patches apply; only the exact focused-qualified test file differs from candidate46')
