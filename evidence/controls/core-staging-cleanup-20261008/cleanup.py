# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess

root = Path.cwd().resolve()
evidence = json.loads((root / 'evidence/core-sdk22-canonical-final-20261007.json').read_text())
rows = json.loads((root / 'results/core-sdk22-staging-cleanup-candidates-20261008.json').read_text())
assert len(rows) == 3 and {row['target'] for row in rows} == {'fedora', 'leap', 'el10'}
ids = subprocess.check_output(['docker', 'ps', '-q'], text=True).split()
containers = json.loads(subprocess.check_output(['docker', 'inspect', *ids], text=True)) if ids else []
verified = []
for row in rows:
    target = row['target']
    base = root / f'results/{target}-core-sdk22-canonical-final-20261007'
    state = json.loads((base / 'build.json').read_text())
    old = evidence['targets'][target]
    assert state['exit_code'] == old['build_exit_code'] == old['installed']['exit_code'] == 0
    assert state['source']['commit'] == evidence['source_commit']
    assert state['artifacts'] == old['installed']['artifacts']
    for name, digest in state['artifacts'].items():
        with (base / name).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest, name
    path = root / row['path']
    assert path.name == 'BUILDROOT' and path.is_dir() and not path.is_symlink()
    assert path.resolve().is_relative_to(base.resolve() / 'rpmbuild')
    subprocess.run(['git', 'check-ignore', '--quiet', str(path.relative_to(root))], check=True)
    for container in containers:
        for mount in container.get('Mounts', []):
            mounted = Path(mount.get('Source', '/nonexistent')).resolve()
            assert not (mounted == base or mounted.is_relative_to(base) or base.is_relative_to(mounted)), container['Id']
    verified.append({**row, 'artifacts_verified': len(state['artifacts']), 'source_commit': state['source']['commit']})
report = {'date_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'authorization': 'User previously requested deletion of unneeded local packaging files.',
          'status': 'All three successful build/install results and every retained RPM hash verified before removal.',
          'preserved': 'RPMs, source archives, logs, source trees, built libraries, documentation and audit/control evidence.',
          'candidates': verified, 'removed': [], 'free_before': shutil.disk_usage(root).free}
record = root / 'results/core-sdk22-staging-cleanup-20261008.json'
record.write_text(json.dumps(report, indent=2) + '\n')
for row in verified:
    path = root / row['path']
    shutil.rmtree(path)
    assert not path.exists()
    report['removed'].append(row['path'])
    record.write_text(json.dumps(report, indent=2) + '\n')
report['free_after'] = shutil.disk_usage(root).free
report['status'] = 'Complete: only the three verified disposable RPM staging directories removed.'
record.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'staging_bytes_removed': sum(row['bytes'] for row in verified),
                  'retained_rpms_verified': sum(row['artifacts_verified'] for row in verified),
                  'free_before': report['free_before'], 'free_after': report['free_after']}))
