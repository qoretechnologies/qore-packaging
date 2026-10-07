# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from datetime import datetime, timezone
import gzip
import hashlib
import json
import re
import shutil
import subprocess

root = Path.cwd()
out = root / 'evidence/controls/nats-candidate46-integration-20261008'
out.mkdir(exist_ok=True)
verification = json.loads((root / 'results/nats-candidate46-patch-verification-20261008.json').read_text())
assert verification['patches'] == 109 and verification['fuzz'] == 0
assert verification['new_patch_offsets'] == 0 and verification['exact_focused_source_identity']
assert verification['changed_go_files_from_candidate45'] == ['server/jetstream_cluster_2_test.go']
bundle = root / 'work/nats-server-candidate-46'
for name, expected in verification['source_manifest']['sources'].items():
    assert hashlib.sha256((bundle / name).read_bytes()).hexdigest() == expected, name
assert (root / 'dependencies/nats-server-meta-api-ready-tests.patch').read_bytes() == (
    root / 'evidence/controls/nats-meta-readiness-20261008/nats-server-meta-api-ready-tests.patch').read_bytes()
assert (root / 'dependencies/nats-server.spec').read_bytes() == (bundle / 'nats-server.spec').read_bytes()
tests = {}
for stem, count in [('tools', 218), ('runner', 7)]:
    path = root / f'results/nats-candidate46-{stem}-tests-20261008.log'
    text = path.read_text()
    assert re.search(r'Ran ' + str(count) + r' tests in [\d.]+s\n\nOK\s*$', text)
    tests[stem] = count
    (out / (path.name + '.gz')).write_bytes(gzip.compress(path.read_bytes(), mtime=0))
ids = subprocess.check_output(['docker', 'ps', '-q'], text=True).split()
containers = json.loads(subprocess.check_output(['docker', 'inspect', *ids], text=True)) if ids else []
active = {}
for container in containers:
    for mount in container['Mounts']:
        for target in ['fedora', 'leap', 'el10']:
            if mount['Source'] == str(root / f'results/{target}-nats-server-candidate-46'):
                assert container['State']['Running']
                active[target] = {'container_id': container['Id'], 'pid': container['State']['Pid'],
                                  'started_at': container['State']['StartedAt'], 'image': container['Image']}
assert set(active) == {'fedora', 'leap', 'el10'}, active
files = ['results/nats-candidate46-patch-verification-20261008.json',
         'results/nats-inactive-cache-cleanup-20261008.json',
         'work/prepare-nats-candidate46-20261008.py',
         'work/build-nats-candidate46-20261008.py']
for name in files:
    shutil.copy2(root / name, out / Path(name).name)
for name in ['results/nats-candidate46-prepare-20261008.log', 'results/nats-candidate46-patches-20261008.log']:
    path = root / name
    (out / (path.name + '.gz')).write_bytes(gzip.compress(path.read_bytes(), mtime=0))
shutil.copy2(Path(__file__), out / 'record.py')
record = {
    'schema': 1, 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'observed_at_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'Qualified metadata-readiness test correction integrated as Patch108; complete three-distribution RPM builds are running.',
    'verification': {key: verification[key] for key in ['patches', 'fuzz', 'new_patch_offsets',
        'changed_go_files_from_candidate45', 'changed_bundle_files', 'exact_focused_source_identity']},
    'focused_qualification': 'evidence/nats-meta-readiness-20261008.json',
    'packaging_tests': tests,
    'active_builds_at_observation': active,
    'disk_cleanup': 'Reclaimed 23,374,925,824 bytes from the inactive reproducible Go compiler cache after checking every running container mount; sources, logs and RPM artifacts are preserved.',
    'remaining': ['Complete candidate46 RPM matrix and review every failure and diagnostic.',
        'Resolve historical sparse-consumer performance, atomic-batch, workqueue and replica-update failures.',
        'Review upstream skips; finish client/module, native OBS, package lint/debug and repository lifecycle qualification.'],
    'limits': ['This is an integration and live-build record, not a claim that candidate46 or NATS is release qualified.',
        'The uncommitted complete NATS dependency stack still awaits all release gates.'],
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
}
(root / 'evidence/nats-candidate46-integration-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('Validated candidate46 bundle and recorded all three live builds, 225 packaging tests and guarded cache cleanup')
