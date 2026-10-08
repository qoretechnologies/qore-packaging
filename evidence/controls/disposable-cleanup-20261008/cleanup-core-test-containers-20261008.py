# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Archive logs and remove only completed core20/core21 qualification containers."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
rows = json.loads((ROOT / 'results/disposable-core-containers-20261008.json').read_text())
assert len(rows) == 36
logs = ROOT / 'results/core-container-cleanup-20261008-logs'
logs.mkdir(exist_ok=False)
images = {}
for row in rows:
    assert re.fullmatch(r'qore-(fedora|leap|el10)-policy-(20|21)-(runtime|sdk)-(install|tests)-(2|3)', row['name'])
    state = json.loads(subprocess.check_output(['docker', 'inspect', row['id']], text=True))[0]
    assert state['Name'].lstrip('/') == row['name'] and state['Image'] == row['image']
    assert state['State']['Status'] == 'exited' and state['State']['ExitCode'] == 0
    assert not state['State']['Running'] and not state['State']['Paused']
    if row['image'] not in images:
        images[row['image']] = json.loads(subprocess.check_output(['docker', 'image', 'inspect', row['image']], text=True))[0]
    content = subprocess.check_output(['docker', 'logs', '--timestamps', row['id']], stderr=subprocess.STDOUT)
    path = logs / (row['name'] + '.log.gz')
    path.write_bytes(gzip.compress(content, mtime=0))
    assert gzip.decompress(path.read_bytes()) == content
    row['log'] = str(path.relative_to(ROOT))
    row['log_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
for row in rows:
    if '-install-' in row['name']:
        tests = next(r for r in rows if r['name'] == row['name'].replace('-install-', '-tests-'))
        before = images[row['image']]['RootFS']['Layers']
        after = images[tests['image']]['RootFS']['Layers']
        assert after[:len(before)] == before and len(after) == len(before) + 1
        row['retained_installed_image'] = tests['image']

report = {
    'schema': 1, 'date_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'authorization': 'User requested removal of unneeded packaging build artifacts.',
    'scope': '36 exited, successful core20/core21 installation and test containers; exact IDs only, no force or volume removal.',
    'preserved': 'All original and installed Docker images, every volume, all live containers, RPMs and source files. Full container logs archived before removal.',
    'containers': rows, 'removed': [], 'free_before': shutil.disk_usage(ROOT).free,
}
record = ROOT / 'results/core-container-cleanup-20261008.json'


def save():
    record.write_text(json.dumps(report, indent=2) + '\n')


save()
for row in rows:
    current = json.loads(subprocess.check_output(['docker', 'inspect', row['id']], text=True))[0]
    assert current['State']['Status'] == 'exited' and current['State']['ExitCode'] == 0
    result = subprocess.check_output(['docker', 'rm', row['id']], text=True).strip()
    assert result == row['id']
    report['removed'].append(row['id'])
    save()
    print('Removed', row['name'], flush=True)
for image in images:
    subprocess.run(['docker', 'image', 'inspect', image], check=True, stdout=subprocess.DEVNULL)
remaining = set(subprocess.check_output(['docker', 'ps', '-aq', '--no-trunc'], text=True).split())
assert not remaining.intersection(report['removed'])
report.update(completed=True, free_after=shutil.disk_usage(ROOT).free)
save()
print(json.dumps({'containers_removed': len(rows), 'images_retained': len(images), 'free_after': report['free_after']}), flush=True)
