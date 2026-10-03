#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Check binary RPM parent-directory ownership against a target RPM database."""
import argparse
import json
from pathlib import Path, PurePosixPath
import shlex
import subprocess


def paths(output):
    """Reject malformed inventories instead of silently losing an ownership check."""
    result = set()
    for line in shlex.split(output):
        path = PurePosixPath(line)
        if (not path.is_absolute() or str(path) != line or '..' in path.parts
                or line.startswith('//') or '\0' in line):
            raise ValueError('Noncanonical RPM payload path: ' + repr(line))
        result.add(line)
    return result


def missing_parents(installed, packages):
    """Return missing ancestors, including intermediate directories, per RPM.

    Sibling binary subpackages may share directory ownership. Installed symlinks
    such as /lib64 are also valid owned ancestors; ownership is not a type check.
    The filesystem root itself does not need an RPM owner.
    """
    owned = set(installed) | {'/'}
    for payload in packages.values():
        owned.update(payload)
    return {name: sorted({str(parent) for entry in payload
                          for parent in PurePosixPath(entry).parents
                          if str(parent) not in owned})
            for name, payload in sorted(packages.items())}


def check(packages):
    # RPM's shell escaping preserves filenames containing whitespace or quotes;
    # parsing these tokens does not execute a shell.
    fmt = '[%{FILENAMES:shescape}\\n]'
    installed = paths(subprocess.check_output(['rpm', '-qa', '--qf', fmt], text=True))
    payloads = {}
    for package in packages:
        package = Path(package).resolve(strict=True)
        if package.suffix != '.rpm' or package.name.endswith(('.src.rpm', '.nosrc.rpm')):
            raise ValueError('Expected a binary RPM: ' + str(package))
        payloads[str(package)] = paths(subprocess.check_output(
            ['rpm', '-qp', '--qf', fmt, '--', str(package)], text=True))
    if not payloads:
        raise ValueError('At least one binary RPM is required')
    return missing_parents(installed, payloads)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packages', nargs='+', type=Path)
    result = check(parser.parse_args().packages)
    print(json.dumps(result, indent=2))
    return int(any(result.values()))


if __name__ == '__main__':
    raise SystemExit(main())
