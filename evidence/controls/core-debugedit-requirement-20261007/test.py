# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import concurrent.futures
import hashlib
import json
import subprocess

root = Path.cwd()
output = root / 'results/core-debugedit-requirement-20261007'
output.mkdir()
source = root / 'work/checkouts/qore-documentation-sdk-20261006'
dependency_root = root / 'results/leap-debugedit-final-1'
dependency = 'rpmbuild/RPMS/x86_64/debugedit-5.1-1.qore.x86_64.rpm'
record = json.loads((dependency_root / 'build.json').read_text())
assert hashlib.sha256((dependency_root / dependency).read_bytes()).hexdigest() == record['artifacts'][dependency]


def run(target):
    record = json.loads((root / f'results/{target}-core-sdk22-canonical-final-20261007/build.json').read_text())
    out = output / target
    out.mkdir()
    script = 'set -eu\nexport QORE_RPM_VERIFY_INSTALLED_DEPS=1\n'
    if target == 'leap':
        script += '''status=0
python3 -B -W error -m unittest discover -s rpm/tests -p test_spec_metadata.py -k indexed_dwarf_build_dependency_resolves -v > /output/old-dependency.log 2>&1 || status=$?
test "$status" -eq 1
python3 - <<'CHECK'
from pathlib import Path
s=Path('/output/old-dependency.log').read_text()
assert 'Ran 1 test' in s and 'FAILED (failures=1)' in s
assert 'Failed build dependencies' in s and 'debugedit >= 5.1' in s
CHECK
'''
        script += 'rpm -U --replacepkgs /dependency/' + dependency + '\n'
    script += 'python3 -B -W error -m unittest discover -s rpm/tests -p test_spec_metadata.py -v\n'
    command = ['docker', 'run', '--rm', '--init', '--network', 'none',
               '-v', str(source) + ':/source:ro', '-v', str(out) + ':/output',
               '-v', str(dependency_root) + ':/dependency:ro', '-w', '/source',
               record['image'], 'sh', '-c', script]
    with (out / 'tests.log').open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=180)
    return {'target': target, 'command': command, 'exit_code': result.returncode}


with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results = list(pool.map(run, ('fedora', 'leap', 'el10')))
(output / 'status.json').write_text(json.dumps(results, indent=2) + '\n')
print({row['target']: row['exit_code'] for row in results})
assert all(row['exit_code'] == 0 for row in results)
