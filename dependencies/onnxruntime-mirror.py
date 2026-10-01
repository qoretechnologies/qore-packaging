#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Populate ONNX Runtime's supported local source mirror from verified inputs."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit


def materialize(source, manifest, archives):
    source, archives = Path(source), Path(archives)
    destination = source / "mirror"
    if destination.exists() or destination.is_symlink():
        raise ValueError("ONNX source mirror already exists")
    upstream = {}
    for line in (source / "cmake/deps.txt").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            name, url, sha1 = line.split(";")
            upstream[name] = (url, sha1)
    payloads = {}
    for name, info in json.loads(Path(manifest).read_text()).items():
        if upstream.get(name) != (info["url"], info["sha1"]):
            raise ValueError("Component differs from ONNX's source pin: " + name)
        url = urlsplit(info["url"])
        relative = Path(url.netloc + url.path)
        if (url.scheme != "https" or url.netloc != "github.com" or url.query or url.fragment
                or ".." in relative.parts or relative.is_absolute()):
            raise ValueError("Unsafe mirror URL")
        filename = info["archive"]
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9+._-]*", filename):
            raise ValueError("Unsafe archive filename")
        path = archives / filename
        if path.is_symlink() or not path.is_file():
            raise ValueError("Component must be a regular archive")
        payload = path.read_bytes()
        if (hashlib.sha256(payload).hexdigest() != info["sha256"]
                or hashlib.sha1(payload).hexdigest() != info["sha1"]):
            raise ValueError("Component checksum mismatch: " + name)
        if relative in payloads:
            raise ValueError("Duplicate component URL")
        payloads[relative] = payload
    if not payloads:
        raise ValueError("Empty component manifest")
    with tempfile.TemporaryDirectory(prefix=".onnx-mirror-", dir=source) as temporary:
        root = Path(temporary) / "mirror"
        root.mkdir()
        for relative, payload in payloads.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        destination.mkdir(exist_ok=False)
        try:
            os.replace(root, destination)
        except BaseException:
            destination.rmdir()
            raise


if __name__ == "__main__":
    materialize(*sys.argv[1:])
