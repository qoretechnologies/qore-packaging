# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib, json, re, subprocess, tarfile

root = Path.cwd()
e = json.loads((root / 'evidence/nats-sparse-index-20261008.json').read_text())
assert e['qualification']['race_results'] == 948 and e['qualification']['nonrace_results'] == 27
for name, expected in e['files_sha256'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
name = 'nats-server-memory-subject-sequences.patch'
assert (root / 'dependencies' / name).read_bytes() == (root / 'evidence/controls/nats-sparse-index-20261008' / name).read_bytes()
patches = re.findall(r'^Patch\d+: (\S+)$', (root / 'dependencies/nats-server.spec').read_text(), re.M)
assert len(patches) == 115 and patches[-1] == name
for filename, count in [('nats-candidate52-tools-tests-20261008.log', 218), ('nats-candidate52-runner-tests-20261008.log', 7)]:
    log = (root / 'results' / filename).read_text()
    assert re.search(r'Ran ' + str(count) + r' tests in [\d.]+s\n\nOK\s*$', log), filename
bundle = root / 'work/nats-server-candidate-52'
out = root / 'work/nats-prepared-52'
source = out / 'nats-server-2.15.0'
with (root / 'results/nats-candidate52-prepare-20261008.log').open('x') as log:
    subprocess.run(['python3', '-B', '-W', 'error', 'tools/prepare-dependency.py', '--name', 'nats-server', '--candidate',
                    '--cache', 'work/nats-server-candidate-51', '--output', str(bundle)], check=True, stdout=log)
out.mkdir()
with tarfile.open(bundle / 'nats-server-2.15.0.tar.gz') as archive:
    archive.extractall(out, filter='data')
with tarfile.open(bundle / 'nats-server-2.15.0-vendor.tar.xz') as archive:
    archive.extractall(source, filter='data')
with (root / 'results/nats-candidate52-patches-20261008.log').open('x') as log:
    for patch in patches:
        result = subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(bundle / patch)], cwd=source,
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log.write(result.stdout)
        assert result.returncode == 0 and 'fuzz' not in result.stdout.lower(), (patch, result.stdout)
        if patch == name:
            assert 'offset' not in result.stdout.lower(), result.stdout
previous = root / 'work/nats-prepared-51/nats-server-2.15.0'
changes = sorted(str(p.relative_to(source)) for p in source.rglob('*.go')
                 if p.is_file() and p.read_bytes() != (previous / p.relative_to(source)).read_bytes())
assert changes == ['server/avl/seqset.go', 'server/avl/seqset_test.go', 'server/memstore.go',
                   'server/memstore_test.go', 'server/store_test.go'], changes
for rel in changes:
    assert hashlib.sha256((source / rel).read_bytes()).hexdigest() == e['source_sha256'][Path(rel).name], rel
manifest = json.loads((bundle / 'source-manifest.json').read_text())
for filename, expected in manifest['sources'].items():
    assert hashlib.sha256((bundle / filename).read_bytes()).hexdigest() == expected, filename
old = json.loads((root / 'work/nats-server-candidate-51/source-manifest.json').read_text())
delta = [p for p, h in manifest['sources'].items() if h != old['sources'].get(p)]
assert sorted(delta) == sorted([name, 'nats-server.spec', 'nats-server.changes']), delta
record = {'schema': 1, 'patches': 115, 'fuzz': 0, 'new_patch_offsets': 0,
          'changed_go_files_from_candidate51': changes, 'changed_bundle_files': delta,
          'exact_focused_source_identity': True, 'qualification': 'evidence/nats-sparse-index-20261008.json',
          'source_manifest': manifest,
          'remaining': 'Historical creation failures, complete combined RPM/native builds and installed client/module/repository qualification remain open.'}
(root / 'results/nats-candidate52-patch-verification-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('All 115 patches apply without fuzz; all five changed Go files match the 975-result qualification.')
