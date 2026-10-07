# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import concurrent.futures
import hashlib
import json
import re
import subprocess
import sys

root = Path.cwd()
label = sys.argv[1]
assert re.fullmatch(r'smoke\d*|all\d*', label)
module = sys.argv[2] if len(sys.argv) > 2 else 'QUnit'
assert re.fullmatch(r'[A-Za-z0-9_]+', module)
output = root / ('results/core-aot-debugger-' + label + '-20261007')
output.mkdir()
dependency_root = root / 'results/leap-debugedit-final-1'
dependency_record = json.loads((dependency_root / 'build.json').read_text())
dependency = 'rpmbuild/RPMS/x86_64/debugedit-5.1-1.qore.x86_64.rpm'
assert hashlib.sha256((dependency_root / dependency).read_bytes()).hexdigest() == dependency_record['artifacts'][dependency]


def qualify(target):
    build = root / f'results/{target}-core-sdk22-canonical-final-20261007'
    record = json.loads((build / 'build.json').read_text())
    assert record['exit_code'] == 0
    sources = list((build / 'rpmbuild/BUILD').glob('qore-*/CMakeLists.txt'))
    sources += list((build / 'rpmbuild/BUILD').glob('qore-*/qore-*/CMakeLists.txt'))
    assert len(sources) == 1
    source = '/work/' + str(sources[0].parent.relative_to(build))
    out = output / target
    out.mkdir()
    options = ' --module ' + module if label.startswith('smoke') else ''
    script = 'set -eu\n'
    if target == 'leap':
        if label.startswith('smoke'):
            script += f'python3 -B -W error /control/control.py --source "{source}" --output /output/old --module {module} --old-debugedit\n'
        script += 'rpm -U --replacepkgs /dependency/' + dependency + '\n'
    script += f'python3 -B -W error /control/control.py --source "{source}" --output /output/new{options}\n'
    command = ['docker', 'run', '--rm', '--init', '--network', 'none',
               '-v', str(build) + ':/work:ro', '-v', str(out) + ':/output',
               '-v', str(dependency_root) + ':/dependency:ro',
               '-v', str(root / 'work/core-aot-debugger-control-20261007.py') + ':/control/control.py:ro',
               record['image'], 'sh', '-c', script]
    with (out / 'driver.log').open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    status = {'target': target, 'command': command, 'exit_code': result.returncode}
    (out / 'status.json').write_text(json.dumps(status, indent=2) + '\n')
    return status


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    records = list(pool.map(qualify, ('fedora', 'leap', 'el10')))
(output / 'status.json').write_text(json.dumps(records, indent=2) + '\n')
print({row['target']: row['exit_code'] for row in records})
assert all(row['exit_code'] == 0 for row in records)
