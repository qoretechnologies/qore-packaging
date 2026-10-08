# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Exercise the actual core identity target after a fingerprinted input edit."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess

root = Path.cwd()
source = root / 'work/checkouts/qore-aot-runtime-dependencies-20261008'
out = root / 'results/aot-runtime-target-order-20261008'
probe = source / 'lib/QoreAOT.cpp'
original = probe.read_bytes()
metadata = probe.stat()
(out / 'source-backup.cpp').write_bytes(original)
original_hash = hashlib.sha256(original).hexdigest()
libraries = json.loads((out / 'before-libraries.json').read_text())
records = []

def digest(build):
    lines = (build / 'qcc-format.stamp').read_text().splitlines()
    expected = hashlib.sha256(('qore-aot-runtime-identity-v1\n' + ''.join(
        line + '\n' for line in lines if not line.startswith('@build-config\t'))).encode()).hexdigest()
    header = (build / 'include/qore/intern/qore_aot_runtime_identity.h').read_text()
    actual = re.search(r'#define QORE_AOT_RUNTIME_IDENTITY "([0-9a-f]{64})"', header).group(1)
    assert actual == expected, (actual, expected)
    return actual

builds = {'release': source / 'build', 'debug': source / 'build-debug'}
before = {mode: digest(build) for mode, build in builds.items()}
assert len(set(before.values())) == 1
for mode, build in builds.items():
    graph = (build / 'CMakeFiles/Makefile2').read_text()
    edge = 'CMakeFiles/qore-aot-runtime-identity.dir/all: CMakeFiles/qcc-format-version.dir/all'
    assert edge in graph
    assert edge not in (out / (mode + '-before-Makefile2')).read_text()
    (out / (mode + '-after-Makefile2')).write_text(graph)

def run(phase, mode, build):
    command = ['cmake', '--build', str(build), '--target', 'qore-aot-runtime-identity', '-j', '8']
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    (out / (phase + '-' + mode + '.log')).write_text(result.stdout)
    assert result.returncode == 0, result.stdout
    assert not re.search(r'(?i)warning:', result.stdout), result.stdout
    value = digest(build)
    records.append({'phase': phase, 'mode': mode, 'command': command,
                    'exit_code': result.returncode, 'identity': value})
    (out / 'input-change-steps.json').write_text(json.dumps(records, indent=2) + '\n')
    return value

try:
    probe.write_bytes(original + b'\n// RPM AOT identity ordering regression control.\n')
    changed_hash = hashlib.sha256(probe.read_bytes()).hexdigest()
    changed = {}
    for mode, build in builds.items():
        changed[mode] = run('changed', mode, build)
        assert changed[mode] != before[mode]
        assert changed_hash in (build / 'qcc-format.stamp').read_text()
    assert len(set(changed.values())) == 1
finally:
    # Restoring bytes is another real input edit. Keep its new mtime until
    # the producer has observed the restoration; backdating it earlier would
    # incorrectly tell Make that the generated fingerprint is still current.
    probe.write_bytes(original)
    try:
        for mode, build in builds.items():
            assert run('restored', mode, build) == before[mode]
            assert hashlib.sha256((build / 'libqore.so.20.0.0').read_bytes()).hexdigest() == libraries[mode]
            assert original_hash in (build / 'qcc-format.stamp').read_text()
    finally:
        os.utime(probe, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
        probe.chmod(metadata.st_mode & 0o777)
        assert hashlib.sha256(probe.read_bytes()).hexdigest() == original_hash

(out / 'input-change-review.json').write_text(json.dumps({
    'status': 'passed', 'cases': 4, 'source_restored_sha256': original_hash,
    'restored_source_mtime_ns': probe.stat().st_mtime_ns,
    'library_hashes_unchanged': libraries, 'identities_before_and_after': before,
    'negative_scope': 'The former generated graph lacked the producer target edge. '
                      'The regression exercises real modified/restored inputs; it does not claim '
                      'deterministically reproducing every previous scheduler interleaving.'
}, indent=2) + '\n')
print('Both actual core target graphs order the fingerprint producer first; edited/restored input checks pass')
