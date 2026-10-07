#!/usr/bin/python3
# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Build a native graph regression with the package's actual V8 ABI and archives."""
import argparse
from pathlib import Path
import shlex
import subprocess


def compile_command(receipt, source, output):
    first = receipt.splitlines()[0] if receipt else ''
    key, separator, command = first.partition(' := ')
    if not separator or not key.startswith('cmd_'):
        raise ValueError('Missing GYP compiler command receipt')
    args = shlex.split(command)
    if (len(args) < 5 or Path(args[0]).name not in ('g++', 'c++')
            or args[1] != '-o' or not args[2].endswith('/raw-machine-assembler.o')
            or not args[3].endswith('/raw-machine-assembler.cc')
            or args.count('-c') != 1 or args.count('-MF') != 1):
        raise ValueError('Unexpected V8 compiler command shape')
    dependency = args.index('-MF') + 1
    if dependency >= len(args) or args[dependency].startswith('-'):
        raise ValueError('Missing dependency receipt filename')
    args[2:4] = [str(output), str(source)]
    args[dependency] = str(output.with_suffix('.d'))
    # The runtime still uses its normal LTO settings. This standalone graph
    # control uses the native sections of the same fat archives, as Memcheck
    # qualification does; all ABI, feature, hardening and warning flags remain.
    args = [arg for arg in args if arg != '-flto' and not arg.startswith('-flto=')
            and arg != '-ffat-lto-objects']
    return [*args, '-fno-lto']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--test-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.source.resolve()
    output = args.output.resolve()
    receipts = list((root / 'out/Release/.deps').rglob('raw-machine-assembler.o.d'))
    if len(receipts) != 1:
        raise ValueError('Expected exactly one native V8 compiler receipt')
    base = root / 'out/Release/obj.target/tools/v8_gypfiles'
    archives = [base / name for name in ('libv8_compiler.a', 'libv8_base_without_compiler.a',
        'libv8_snapshot.a', 'libv8_libbase.a', 'libabseil.a', 'libv8_zlib.a',
        'libhighway.a', 'libsimdutf.a')]
    if not all(path.is_file() for path in archives):
        raise FileNotFoundError('Complete native V8 archives, including its snapshot, are required')
    command = compile_command(receipts[0].read_text(), args.test_source.resolve(), output.with_suffix('.o'))
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(command, cwd=root / 'out', check=True)
    subprocess.run([command[0], '-fno-lto', '-pthread', '-Wl,--gc-sections',
        str(output.with_suffix('.o')), '-Wl,--start-group', *map(str, archives),
        '-Wl,--end-group', '-lz', '-licui18n', '-licuuc', '-ldl', '-lrt',
        '-o', str(output)], cwd=root / 'out', check=True)
    subprocess.run([str(output)], check=True)


if __name__ == '__main__':
    main()
