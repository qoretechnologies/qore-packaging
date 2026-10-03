#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Check real mount capacity, isolation, execution and unprivileged cleanup."""
import os
from pathlib import Path
import subprocess
import tempfile


def available():
    stat = os.statvfs('/tmp')
    return stat.f_bavail * stat.f_frsize


assert os.getuid() != 0
assert os.stat('/tmp').st_dev != os.stat('/work').st_dev
stat = os.statvfs('/tmp')
assert stat.f_blocks * stat.f_frsize == 128 * 1024 * 1024
assert os.stat('/tmp').st_mode & 0o7777 == 0o1777
with tempfile.TemporaryDirectory(dir='/tmp') as temporary:
    root = Path(temporary)
    executable = root / 'executable'
    executable.write_text('#!/bin/sh\nexit 42\n')
    executable.chmod(0o700)
    assert subprocess.run([str(executable)], check=False).returncode == 42
    before = available()
    # Writes on the shared build volume must not change this test's capacity.
    with tempfile.TemporaryFile(dir='/work') as external:
        external.write(b'x' * (8 * 1024 * 1024))
        external.flush()
        os.fsync(external.fileno())
        assert available() == before
    with tempfile.TemporaryFile(dir=root) as internal:
        internal.write(b'x' * (8 * 1024 * 1024))
        internal.flush()
        assert before - available() == 8 * 1024 * 1024
    assert available() == before
assert not root.exists()
print('PASS: bounded private /tmp, external-write isolation, executable tests and cleanup')
