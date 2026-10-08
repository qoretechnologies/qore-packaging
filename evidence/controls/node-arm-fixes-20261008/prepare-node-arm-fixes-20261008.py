# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib
import json
import re
import subprocess
import tarfile

root = Path.cwd()
out = root / 'work/nodejs24-libnode-arm-fixes-candidate-20261008'
result = root / 'results/node-arm-source-final-20261008'
result.mkdir()
assert out.is_dir()  # Reuse the already prepared and verified candidate payload.
manifest = json.loads((out / 'source-manifest.json').read_text())
previous = json.loads((root / 'work/nodejs24-libnode-obs-fixtures-20261008/source-manifest.json').read_text())
changed = sorted(name for name, digest in manifest['sources'].items()
                 if previous['sources'].get(name) != digest)
assert changed == sorted(['nodejs24-libnode.spec', 'nodejs24-libnode.changes',
    'nodejs24-arm-header-operand.patch', 'nodejs24-arm-cpu-feature-guard.patch',
    'nodejs24-arm-header-test.py', 'nodejs24-arm-operand-test.cc']), changed
assert set(previous['sources']) <= set(manifest['sources'])
for name, digest in manifest['sources'].items():
    assert hashlib.sha256((out / name).read_bytes()).hexdigest() == digest, name
recipe = (out / 'nodejs24-libnode.spec').read_text()
assert recipe == (root / 'dependencies/nodejs24-libnode.spec').read_text()
config = json.loads((root / 'dependencies/sources.json').read_text())['nodejs24-libnode']
for name in config['extra_sources']:
    assert (out / name).read_bytes() == (root / 'dependencies' / name).read_bytes(), name
patches = re.findall(r'^Patch\d+:\s*(\S+)', recipe, re.M)
assert len(patches) == 24
files = set()
for name in patches:
    files.update(re.findall(r'^--- a/(.+)$', (out / name).read_text(), re.M))
tree = result / 'source'
tree.mkdir()
with tarfile.open(out / 'node-v24.18.1.tar.xz') as archive:
    for name in sorted(files):
        member = archive.getmember('node-v24.18.1/' + name)
        assert member.isfile()
        target = tree / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with archive.extractfile(member) as stream:
            target.write_bytes(stream.read())
with (result / 'patches.log').open('x') as log:
    for patch in patches:
        subprocess.run(['patch', '-p1', '--fuzz=0', '--batch', '-i', str(out / patch)],
                       cwd=tree, stdout=log, stderr=subprocess.STDOUT, check=True)
patch_log = (result / 'patches.log').read_text()
assert not re.search(r'fuzz|FAILED', patch_log, re.I)
assert re.findall(r'^Hunk .*$', patch_log, re.M) == ['Hunk #1 succeeded at 2978 (offset -1 lines).']
assert 'patching file deps/v8/src/objects/intl-objects.cc\nHunk #1 succeeded at 2978 (offset -1 lines).' in patch_log
tested = {
    'deps/v8/src/regexp/arm64/regexp-macro-assembler-arm64.h': 'work/node-arm-header-20261008/regexp-macro-assembler-arm64.h',
    'deps/v8/src/regexp/arm64/regexp-macro-assembler-arm64.cc': 'work/node-arm-header-20261008/regexp-macro-assembler-arm64.cc',
    'deps/v8/third_party/zlib/cpu_features.c': 'work/node-arm-zlib-20261008/cpu_features.c',
    'test/parallel/test-process-euid-egid.js': 'results/node-obs-fixtures2-20261008/fixed.js',
}
for name, expected in tested.items():
    assert (tree / name).read_bytes() == (root / expected).read_bytes(), name
canonical = root / 'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
for name in files - tested.keys():
    assert (tree / name).read_bytes() == (canonical / name).read_bytes(), name
image = 'sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414'
for arch in ('x86_64', 'aarch64'):
    command = ['docker', 'run', '--rm', '--network', 'none', '-v', str(out) + ':/sources:ro',
               image, 'rpmspec', '-P', '--target', arch, '--define', '_sourcedir /sources',
               '/sources/nodejs24-libnode.spec']
    check = subprocess.run(command, text=True, capture_output=True, check=True)
    assert not check.stderr, check.stderr
    assert ('python3 /sources/nodejs24-arm-header-test.py' in check.stdout) == (arch == 'aarch64')
    (result / (arch + '.spec')).write_text(check.stdout)
(result / 'verification.json').write_text(json.dumps({
    'patches': len(patches), 'zero_fuzz': True, 'new_patches_zero_offset': True,
    'existing_offset': 'Patch16 timezone-index applies one line earlier after Patch14; complete resulting source matches the already qualified canonical build.',
    'other_qualified_source_files_unchanged': len(files - tested.keys()),
    'all_source_hashes_verified': len(manifest['sources']), 'changed_sources': changed,
    'qualified_source_sha256': {name: hashlib.sha256((tree / name).read_bytes()).hexdigest() for name in tested},
    'spec_architectures': ['x86_64', 'aarch64'], 'native_arm_check_selected_only_on_arm': True,
}, indent=2) + '\n')
print('All 24 patches apply without fuzz; new patches have no offset; all sources match qualified files and both architecture recipes parse.')
