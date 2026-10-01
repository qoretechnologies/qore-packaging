#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Exercise bounded descriptor use, chunk boundaries and parallel normalization."""
import hashlib
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile

bindir = Path(sys.argv[1]).resolve()

def limited_descriptors():
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    # Hundreds of equal-size files differ in their first 4 KiB hash. The old
    # sorter retained descriptors for them even after distinguishing them.
    groups = []
    for n in range(192):
        data = hashlib.sha256(str(n).encode()).digest() * 256
        groups.append(data)
    # Equal prefixes force reads across the increasing hash chunk boundaries.
    for length in (0, 4095, 4096, 4097, 12288, 12289, 30000):
        for suffix in (b"a", b"b"):
            groups.append(b"x" * length + suffix)
    expected = {}
    for n, data in enumerate(groups):
        for copy in ("a", "b"):
            path = root / f"{n:04}-{copy}"
            path.write_bytes(data)
            expected[path] = data
    env = {**os.environ, "RPM_BUILD_ROOT": directory}
    subprocess.run([str(bindir / "linkdupes"), "--brp", "--ignore-mtime", directory],
                   env=env, preexec_fn=limited_descriptors, check=True)
    for n, data in enumerate(groups):
        a, b = (root / f"{n:04}-{copy}" for copy in ("a", "b"))
        assert a.stat().st_ino == b.stat().st_ino, n
    assert len({p.stat().st_ino for p in expected}) == len(set(groups))
    for path, data in expected.items():
        assert path.read_bytes() == data, path
    # A second pass must preserve bytes, paths and hardlinks.
    subprocess.run([str(bindir / "linkdupes"), "--brp", "--ignore-mtime", directory],
                   env=env, preexec_fn=limited_descriptors, check=True)
    assert set(root.iterdir()) == set(expected)
    for path, data in expected.items():
        assert path.read_bytes() == data, path
print("descriptor, chunk-boundary, content and idempotence checks passed")
