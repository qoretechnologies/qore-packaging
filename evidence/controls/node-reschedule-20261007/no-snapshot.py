# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import shlex
import subprocess

root = Path('/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1')
out = Path('/control')
line = next(line for line in Path('/work/build.log').open()
            if line.strip().startswith('g++ -o ') and 'raw-machine-assembler.o ' in line)
args = shlex.split(line)
args = [arg for arg in args if not arg.startswith('-flto=') and arg != '-ffat-lto-objects']
args.append('-fno-lto')
records = []

def run(name, command):
    with (out / (name + '.log')).open('x') as log:
        result = subprocess.run(command, cwd=root / 'out', stdout=log, stderr=subprocess.STDOUT)
    records.append(dict(name=name, command=command, exit_code=result.returncode))
    (out / 'no-snapshot-status.json').write_text(json.dumps(records, indent=2) + '\n')
    result.check_returncode()

# The control builds graphs only: it creates no Isolate, executes no generated
# code and requires no startup snapshot. Use V8's unmodified no-snapshot sources.
objects = []
for name in ('src/snapshot/snapshot-empty.cc',
             'src/snapshot/embedded/embedded-empty.cc',
             'src/init/setup-isolate-deserialize.cc'):
    obj = out / (Path(name).stem + '.o')
    command = args.copy()
    command[2:4] = [str(obj), str(root / 'deps/v8' / name)]
    command[command.index('-MF') + 1] = str(obj.with_suffix('.d'))
    run(Path(name).stem + '-compile', command)
    objects.append(str(obj))
base = root / 'out/Release/obj.target/tools/v8_gypfiles'
run('no-snapshot-link', ['g++', '-fno-lto', '-pthread', '-Wl,--gc-sections',
    '/control/control.o', *objects, '-Wl,--start-group',
    *[str(base / name) for name in ('libv8_compiler.a', 'libv8_base_without_compiler.a',
       'libv8_libbase.a', 'libabseil.a', 'libv8_zlib.a', 'libhighway.a', 'libsimdutf.a')],
    '-Wl,--end-group', '-lz', '-licui18n', '-licuuc', '-ldl', '-lrt', '-o', '/control/original'])
run('no-snapshot-normal', ['/control/original'])
run('no-snapshot-memory', ['valgrind', '--error-exitcode=99', '--leak-check=full',
    '--errors-for-leak-kinds=all', '--log-file=/control/no-snapshot-valgrind.log', '/control/original'])
