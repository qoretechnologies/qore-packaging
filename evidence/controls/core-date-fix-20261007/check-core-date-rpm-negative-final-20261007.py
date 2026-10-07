# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import subprocess

root = Path.cwd()
repo = root.parent / 'qore'
out = root / 'results/core-date-rpm-negative-final-20261007'
out.mkdir()


def run(target):
    record = json.loads((root / f'results/{target}-core-sdk22-canonical-final-installed-20261007.json').read_text())
    script = '''set -eu
c++ -std=c++20 -O2 -g -Wall -Werror /control/date_add.cpp -lqore -o /tmp/date-add
status=0
/tmp/date-add > /tmp/result.log 2>&1 || status=$?
cat /tmp/result.log
test "$status" -eq 1
test "$(cat /tmp/result.log)" = 'FAIL after 0 cases: DateTime::add returned the wrong date'
'''
    command = ['docker', 'run', '--rm', '--init', '--network', 'none', '-v',
        str(repo / 'examples/test/qore/vars/date_add.cpp') + ':/control/date_add.cpp:ro',
        record['sdk_image'], 'sh', '-c', script]
    with (out / (target + '.log')).open('x') as stream:
        result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, timeout=120)
    assert result.returncode == 0, (target, (out / (target + '.log')).read_text())
    return {'target': target, 'command': command, 'exit_code': result.returncode,
            'old_library_expected_failure': True}


with ThreadPoolExecutor(max_workers=3) as pool:
    rows = list(pool.map(run, ('fedora', 'leap', 'el10')))
(out / 'status.json').write_text(json.dumps(rows, indent=2) + '\n')
print('PASS: all three installed core22 SDKs reproduce the native date addition defect')
