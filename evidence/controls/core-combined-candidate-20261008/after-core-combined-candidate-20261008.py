# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Join the existing build and qualify its immutable Fedora/EL candidate RPMs."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import select
import subprocess

root = Path('/home/david/src/qore/git/qore-packaging')
os.chdir(root)
output = root / 'results/core-combined-installed-followup-20261008.json'
assert not output.exists(), 'Do not start a second qualifier'
build_status = root / 'results/core-fixes-combined-candidate-20261008-status.json'
build = json.loads(build_status.read_text())
state = {'pid': os.getpid(), 'build_pid': build['pid'], 'steps': {},
         'status': 'joining existing build process', 'qualification_only': True}


def save():
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(state, indent=2) + '\n')
    temporary.replace(output)


def qualify(target):
    log = root / f'results/{target}-core-combined-installed-driver-20261008.log'
    with log.open('x') as stream:
        result = subprocess.run(
            ['python3', '-B', '-W', 'error',
             'work/qualify-core-combined-candidate-20261008.py', target],
            stdout=stream, stderr=subprocess.STDOUT)
    return target, result.returncode


save()
try:
    try:
        descriptor = os.pidfd_open(build['pid'])
    except ProcessLookupError:
        descriptor = None
    if descriptor is not None:
        try:
            command = Path(f"/proc/{build['pid']}/cmdline").read_bytes()
            assert b'work/build-core-fixes-combined-candidate-20261008.py' in command
            select.select([descriptor], [], [])
        finally:
            os.close(descriptor)
    build = json.loads(build_status.read_text())
    assert build['exit_code'] == 0, build
    for target in ('fedora', 'el10'):
        directory = root / f'results/{target}-core-fixes-combined-candidate-20261008'
        manifest = json.loads((directory / 'build.json').read_text())
        assert manifest['exit_code'] == 0, target
        assert manifest['source']['candidate'] is True, target
        assert len(manifest['source']['source_overlay']) == 65, target
        assert 'Passed 405 out of 405 tests. 0 tests failed.' in (directory / 'build.log').read_text()
    state['status'] = 'qualifying installed Fedora and EL candidates'
    save()
    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in as_completed([pool.submit(qualify, target) for target in ('fedora', 'el10')]):
            target, code = future.result()
            state['steps'][target] = code
            save()
            print(target, code, flush=True)
    state['exit_code'] = int(any(state['steps'].values()))
    state['status'] = 'complete'
except BaseException as error:
    state['exit_code'] = 1
    state['error'] = str(error)
    raise
finally:
    save()
raise SystemExit(state['exit_code'])
