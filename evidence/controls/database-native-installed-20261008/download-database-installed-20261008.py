# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import io
import json
import subprocess
import zipfile

root = Path.cwd()
out = root / 'results/database-installed-native-20261008'
out.mkdir()
project = 'projects/mirror%2Fqore-packaging'

def download(case):
    target, job = case
    folder = out / target
    folder.mkdir()
    detail = json.loads(subprocess.check_output(['glab', 'api', f'{project}/jobs/{job}']))
    assert detail['pipeline']['id'] == 59974
    assert detail['status'] == ('failed' if target == 'el10' else 'success')
    (folder / 'job.json').write_text(json.dumps(detail, indent=2) + '\n')
    data = subprocess.check_output(['glab', 'api', f'{project}/jobs/{job}/artifacts'])
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert sum(i.file_size for i in archive.infolist()) < 100_000_000
        for name in archive.namelist():
            p = Path(name)
            assert not p.is_absolute() and '..' not in p.parts and p.parts[:2] == ('results', 'native-installed')
        archive.extractall(folder)
    if target != 'el10':
        q = json.loads((folder / 'results/native-installed/qualification.json').read_text())
        assert q['exit_code'] == 0 and q['machine'] == 'aarch64'
        assert all(s['exit_code'] == 0 for s in q['steps'])
        assert q['manifest'] == json.loads((root / f'qualification/databases-{target}-aarch64.json').read_text())
        names = {s['name'] for s in q['steps']}
        assert {'runtime-freetds-tests', 'sdk-freetds-tests', 'runtime-mysql-tests', 'sdk-mysql-tests',
                'runtime-runtime', 'sdk-runtime', 'sdk-development', 'sdk-tools', 'sdk-remote-debuggers'} <= names
    print(target, detail['status'], flush=True)

with ThreadPoolExecutor(max_workers=3) as pool:
    list(pool.map(download, [('fedora', 209696), ('leap', 209697), ('el10', 209698)]))
