# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import shlex
import subprocess

root = Path('/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1')
out = Path('/control')
line = next(line for line in Path('/work/build.log').open()
            if line.strip().startswith('g++ -o ') and 'raw-machine-assembler.o ' in line)
args = [arg for arg in shlex.split(line) if not arg.startswith('-flto=') and arg != '-ffat-lto-objects']
args.extend(['-fno-lto', '-I/diagnostic-headers'])
records = []

def run(name, command, expected=0):
    with (out / (name + '2.log')).open('x') as log:
        result = subprocess.run(command, cwd=root / 'out', stdout=log, stderr=subprocess.STDOUT)
    records.append(dict(name=name, command=command, exit_code=result.returncode, expected=expected))
    (out / 'instrumented-status.json').write_text(json.dumps(records, indent=2) + '\n')
    assert result.returncode == expected, (name, result.returncode, expected)

def compile(name, source):
    obj = out / (name + '.o')
    command = args.copy()
    command[2:4] = [str(obj), str(source)]
    command[command.index('-MF') + 1] = str(obj.with_suffix('.d'))
    run(name + '-compile', command)
    return str(obj)

control = str(out / 'control-seven.o')
base = root / 'out/Release/obj.target/tools/v8_gypfiles'
objects = [str(out / (name + '.o')) for name in
    ('snapshot-empty', 'embedded-empty', 'setup-isolate-deserialize')]
for name in ('original-instrumented', 'fixed-instrumented'):
    obj = compile(name, out / (name + '-raw.cc'))
    binary = str(out / (name + '-seven'))
    run(name + '-link', ['g++', '-fno-lto', '-pthread', '-Wl,--gc-sections', control, obj,
        *objects, '-Wl,--start-group', *[str(base / name) for name in
        ('libv8_compiler.a', 'libv8_base_without_compiler.a', 'libv8_libbase.a',
         'libabseil.a', 'libv8_zlib.a', 'libhighway.a', 'libsimdutf.a')],
        '-Wl,--end-group', '-lz', '-licui18n', '-licuuc', '-ldl', '-lrt', '-o', binary])
    run(name + '-normal', [binary])
    run(name + '-memory', ['valgrind', '--error-exitcode=99', '--leak-check=full',
        '--errors-for-leak-kinds=all', '--log-file=' + str(out / (name + '-seven-valgrind.log')),
        binary], 99 if name == 'original-instrumented' else 0)
