#!/usr/bin/env python3
# Copyright (C) 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Compile the installed PDFium C API consumer using its public pkg-config contract."""
import argparse
from pathlib import Path
import shlex
import subprocess

SOURCE = Path(__file__).resolve().parents[1] / 'dependencies/pdfium-api-test.c'


def build_api(output):
    flags = {}
    for option in ('--cflags', '--libs'):
        flags[option] = shlex.split(subprocess.check_output(
            ['pkg-config', option, 'pdfium-qore'], text=True))
    # -UNDEBUG preserves the consumer's functional assertions regardless of the
    # distribution's usual Release convention. No source-tree include/link paths.
    subprocess.run(['cc', '-std=c11', '-O2', '-g', '-Wall', '-Wextra', '-Werror', '-UNDEBUG',
                    *flags['--cflags'], str(SOURCE), *flags['--libs'], '-o', str(output)], check=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    build_api(parser.parse_args().output)
