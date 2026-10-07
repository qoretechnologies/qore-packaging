#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Set installed RPM interpreters and normalize generated notice line endings."""
import argparse
from pathlib import Path


INTERPRETERS = {
    **{'usr/bin/' + name: b'qore' for name in
       ('qjavac', 'qjava2jar', 'qjava-migrate-imports', 'qkotlinc')},
    **{'usr/share/qore/java/kotlin/bin/' + name: b'bash' for name in
       ('kapt', 'kotlin', 'kotlinc', 'kotlinc-js', 'kotlinc-jvm')},
}


def regular_file(root, path):
    if (not path.is_file() or path.is_symlink() or root.is_symlink()
            or not path.resolve().is_relative_to(root.resolve())
            or any(p.is_symlink() for p in path.parents if p.is_relative_to(root))):
        raise ValueError('Expected a regular staged file: ' + str(path))
    return path.read_bytes()


def normalize(root, docdir):
    root, docdir = Path(root), Path(docdir)
    if not docdir.is_absolute() or docdir == Path('/') or '..' in docdir.parts:
        raise ValueError('Documentation prefix must be absolute without parent traversal')
    changes = {}
    # Validate the complete expected inventory before changing staged files.
    for relative, interpreter in INTERPRETERS.items():
        path = root / relative
        data = regular_file(root, path)
        first, separator, body = data.partition(b'\n')
        wanted = b'#!/usr/bin/' + interpreter
        if first not in (b'#!/usr/bin/env ' + interpreter, wanted) or not separator:
            raise ValueError('Unexpected installed script interpreter: ' + relative)
        if first != wanted:
            changes[path] = wanted + separator + body
    notices = root / docdir.relative_to('/') / 'qore-jni-module/third-party-notices'
    if not notices.is_dir() or notices.is_symlink():
        raise ValueError('Missing staged third-party notices')
    files = sorted(notices.glob('*.jar.txt'))
    if not files:
        raise ValueError('Missing generated JAR notices')
    for path in files:
        data = regular_file(root, path)
        normalized = data.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
        if normalized != data:
            changes[path] = normalized
    # A failed staging write fails the build; no partial package is published.
    for path, data in changes.items():
        path.write_bytes(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--docdir', type=Path, required=True)
    args = parser.parse_args()
    normalize(args.root, args.docdir)
