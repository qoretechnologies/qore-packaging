#!/usr/bin/env python3
# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Reject obsolete libc resolver imports, while permitting c-ares functions."""
import argparse
import subprocess


OBSOLETE = frozenset(base + suffix for base in
                     ('gethostbyname', 'gethostbyname2', 'gethostbyaddr')
                     for suffix in ('', '_r'))


def obsolete_imports(nm_output):
    return sorted({line.split()[-1].split('@', 1)[0]
                   for line in nm_output.splitlines() if line.split()
                   if line.split()[-1].split('@', 1)[0] in OBSOLETE})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('library')
    args = parser.parse_args()
    symbols = subprocess.check_output(['nm', '-D', '--undefined-only', args.library], text=True)
    obsolete = obsolete_imports(symbols)
    if obsolete:
        parser.exit(1, 'Obsolete libc resolver imports: ' + ', '.join(obsolete) + '\n')


if __name__ == '__main__':
    main()
