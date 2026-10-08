#!/usr/bin/python3
# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Check the ARM64 regexp header and actual Operand types with native build flags."""
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
    stem = 'regexp-macro-assembler-arm64'
    if (len(args) < 5 or Path(args[0]).name not in ('g++', 'c++')
            or args[1] != '-o' or not args[2].endswith('/' + stem + '.o')
            or not args[3].endswith('/' + stem + '.cc')
            or '-DV8_TARGET_ARCH_ARM64' not in args
            or args.count('-c') != 1 or args.count('-MF') != 1):
        raise ValueError('Unexpected ARM64 compiler command shape')
    dependency = args.index('-MF') + 1
    if dependency >= len(args) or args[dependency].startswith('-'):
        raise ValueError('Missing dependency receipt filename')
    args[2:4] = [str(output), str(source)]
    args[dependency] = str(output.with_suffix('.d'))
    # These standalone header/type controls use native object code. The Node
    # runtime retains its normal LTO; ABI, feature and hardening flags survive.
    args = [arg for arg in args if arg != '-flto' and not arg.startswith('-flto=')
            and arg != '-ffat-lto-objects']
    return [*args, '-fno-lto', '-Werror']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--test-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.source.resolve()
    output = args.output.resolve()
    receipts = list((root / 'out/Release/.deps').rglob('regexp-macro-assembler-arm64.o.d'))
    if len(receipts) != 1:
        raise ValueError('Expected exactly one native ARM64 regexp compiler receipt')
    receipt = receipts[0].read_text()
    output.parent.mkdir(parents=True, exist_ok=True)
    probe = output.with_suffix('.header.cc')
    probe.write_text('// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT\n'
                     '#include "src/regexp/arm64/regexp-macro-assembler-arm64.h"\n')
    for source, target in [(probe, output.with_suffix('.header.o')),
                           (args.test_source.resolve(), output.with_suffix('.o'))]:
        command = compile_command(receipt, source, target)
        subprocess.run(command, cwd=root / 'out', check=True)
    subprocess.run([command[0], '-fno-lto', '-pthread', str(output.with_suffix('.o')),
                    '-o', str(output)], check=True)
    subprocess.run([str(output)], check=True)


if __name__ == '__main__':
    main()
