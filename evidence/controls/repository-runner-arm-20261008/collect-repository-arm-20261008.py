# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Join native job log streams and collect their terminal state and artifacts."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath
import json
import subprocess
import zipfile

root = Path(__file__).resolve().parent.parent
out = root / 'results/repository-runner-arm-20261008'
out.mkdir()
jobs = json.loads((root / 'results/repository-runner-arm-jobs-20261008.json').read_text())
expected = '8f83585ca07a4a54704e35b01828ad7d23753de1'


def collect(job):
    name = job['name']
    directory = out / name
    directory.mkdir()
    with (directory / 'trace.log').open('x') as stream:
        trace = subprocess.run(['glab', 'ci', 'trace', str(job['id']), '-R',
                                'https://git.qoretechnologies.com/mirror/qore-packaging'],
                               stdout=stream, stderr=subprocess.STDOUT)
    endpoint = 'projects/mirror%2Fqore-packaging/jobs/' + str(job['id'])
    details = json.loads(subprocess.check_output(['glab', 'api', '--hostname', 'git.qoretechnologies.com', endpoint]))
    (directory / 'job.json').write_text(json.dumps(details, indent=2) + '\n')
    assert details['pipeline']['id'] == 60058 and details['commit']['id'] == expected
    assert details['status'] in ('success', 'failed', 'canceled') and details['finished_at']
    if name != 'packaging-tools':
        archive = directory / 'artifacts.zip'
        with archive.open('xb') as stream:
            process = subprocess.run(['glab', 'api', '--hostname', 'git.qoretechnologies.com', endpoint + '/artifacts'],
                                     stdout=stream, stderr=subprocess.PIPE)
        (directory / 'artifact-download.stderr').write_bytes(process.stderr)
        process.check_returncode()
        with zipfile.ZipFile(archive) as bundle:
            for item in bundle.infolist():
                path = PurePosixPath(item.filename)
                assert not path.is_absolute() and '..' not in path.parts
                assert path.parts[:2] == ('results', 'native-installed')
                if item.is_dir():
                    continue
                assert (item.external_attr >> 16) & 0o170000 != 0o120000
                destination = directory.joinpath(*path.parts[2:])
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(bundle.read(item))
    result = {'job_id': job['id'], 'status': details['status'], 'trace_exit_code': trace.returncode,
              'web_url': details['web_url']}
    (directory / 'collection.json').write_text(json.dumps(result, indent=2) + '\n')
    print(name, result, flush=True)
    return name, result


with ThreadPoolExecutor(max_workers=4) as pool:
    results = dict(pool.map(collect, jobs))
(out / 'status.json').write_text(json.dumps(results, indent=2) + '\n')
raise SystemExit(any(result['status'] != 'success' for result in results.values()))
