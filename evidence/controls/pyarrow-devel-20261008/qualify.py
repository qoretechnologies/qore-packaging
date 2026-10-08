#!/usr/bin/python3
# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Check built PyArrow package ownership, upgrade, runtime, SDK and lint."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--build', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[3]
build = args.build.resolve()
out = args.output.resolve()
out.mkdir()
manifest = json.loads((build / 'build.json').read_text())
assert manifest['exit_code'] == 0
record = {'source': manifest['source'], 'steps': []}


def run(name, command):
    with (out / (name + '.log')).open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=1800)
    record['steps'].append({'name': name, 'command': command, 'exit_code': result.returncode})
    (out / 'status.json').write_text(json.dumps(record, indent=2) + '\n')
    result.check_returncode()


artifacts = {}
for rel, digest in manifest['artifacts'].items():
    with (build / rel).open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest
    artifacts[Path(rel).name] = '/rpms/' + rel
runtime = next(p for n, p in artifacts.items() if n.startswith('python313-pyarrow-25.'))
devel = next(p for n, p in artifacts.items() if n.startswith('python313-pyarrow-devel-'))
srpm = next(p for n, p in artifacts.items() if n.endswith('.src.rpm'))
mounts = ['-v', str(build) + ':/rpms:ro', '-v', str(out) + ':/output',
          '-v', str(root / 'dependencies/pyarrow-runtime-test.py') + ':/runtime-test.py:ro']

# Query both RPMs before installation; reject overlap or runtime header ownership.
query = '''import json, subprocess
from pathlib import Path
runtime, devel = __import__('sys').argv[1:]
def files(rpm):
    return set(subprocess.check_output(['rpm', '-qpl', rpm], text=True).splitlines())
r, d = files(runtime), files(devel)
shared = r & d
assert all('/licenses/' in p or p.endswith('/licenses') for p in shared), shared
headers = {p for p in d if p.endswith(('.h', '.hpp'))}
assert len(headers) == 395, len(headers)
assert not any(p.endswith(('.h', '.hpp')) for p in r)
requires = subprocess.check_output(['rpm', '-qp', '--requires', devel], text=True).splitlines()
assert 'python313-pyarrow = 25.0.1-2.qore' in requires, requires
assert 'apache-arrow-devel = 25.0.1' in requires, requires
assert 'python313-devel' in requires, requires
assert 'python313-numpy-devel >= 1.25' in requires, requires
assert 'python(abi) = 3.13' in requires, requires
Path('/output/ownership.json').write_text(json.dumps({'headers': len(headers), 'runtime_files': len(r), 'devel_files': len(d), 'requires': requires}, indent=2)+chr(10))
print('PASS: 395 development headers; no runtime headers; exact runtime/Arrow dependencies')
'''
run('ownership', ['docker', 'run', '--rm', '--network', 'none', *mounts,
    'qore-rpm-keep:leap-grpcio14b-bridge-sdk-1', 'python3', '-B', '-W', 'error', '-c', query, runtime, devel])
run('runtime-upgrade', ['docker', 'run', '--rm', '--network', 'none', *mounts,
    'qore-rpm-keep:leap-grpcio14b-bridge-runtime-1', 'sh', '-ec', '''
rpm -Uvh --includedocs "$1"
for package in python313-pyarrow-devel python313-devel gcc-c++; do
    if rpm -q "$package"; then
        echo "Unexpected SDK package in runtime fixture: $package" >&2
        exit 1
    fi
done
python3 -B -W error -c 'import pyarrow; from pathlib import Path; p=Path(pyarrow.__file__).parent; assert not (p/"include").exists(); assert not (p/"src").exists(); assert "Package marker" in (p/"includes/__init__.pxd").read_text()'
python3 -B -W error -m pytest -v /runtime-test.py
''', 'runtime', runtime])
# Test real Cython C imports, generated C++ compilation, linking and import.
consumer = out / 'consumer.pyx'
consumer.write_text('''# Copyright 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
from pyarrow.lib cimport Array
cimport pyarrow.includes

def length(Array value):
    return len(value)
''')
sdk = r'''
rpm -Uvh --includedocs "$1" "$2"
python3 -B -W error -m pytest -v /runtime-test.py
cd /output
python3 -B -W error - <<'CHECK'
import importlib, pathlib, subprocess, sys, sysconfig
import pyarrow, numpy
headers=pyarrow.get_include()
assert pathlib.Path(headers, 'arrow/python/pyarrow.h').is_file()
subprocess.run([sys.executable, '-m', 'cython', '--cplus', '-3', 'consumer.pyx'], check=True)
ext='consumer'+sysconfig.get_config_var('EXT_SUFFIX')
subprocess.run(['c++', '-shared', '-fPIC', '-O2', '-std=c++20', '-I'+headers,
               '-I'+sysconfig.get_path('include'), '-I'+numpy.get_include(),
               'consumer.cpp', '-o', ext], check=True)
consumer=importlib.import_module('consumer')
for values in ([], [None], [1, None, 3], list(range(1024))):
    assert consumer.length(pyarrow.array(values)) == len(values)
try:
    consumer.length('invalid')
except TypeError:
    pass
else:
    raise AssertionError('typed Cython API accepted an invalid array')
print('PASS: Cython package marker and real PyArrow extension consumer, including empty/null/invalid input')
CHECK
rpm -e python313-pyarrow-devel
python3 -B -W error -m pytest -v /runtime-test.py
'''
run('sdk-consumer-and-removal', ['docker', 'run', '--rm', '--network', 'none', *mounts,
    'qore-rpm-keep:leap-pyarrow-devel-builddeps-20261008', 'sh', '-ec', sdk, 'sdk', runtime, devel])
run('lint', ['docker', 'run', '--rm', '--network', 'none', *mounts,
    'qore-rpm-keep:leap-pdfium-installed-8', 'rpmlint', runtime, devel, srpm])
assert '0 errors, 0 warnings' in (out / 'lint.log').read_text()
print('PASS: ownership, runtime upgrade, SDK consumer, SDK removal and target RPM lint')
