# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Stage the reviewed XML test fixtures without checkout modules or binaries."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile

from packaging import fetch_source

COMMIT = 'd32601505b85b07823f98cc006fe438baa6dd3bc'
SOURCE_REVISION = 'd672a36fd359885da3559de45cb2482d'
ARCHIVE_ROOT = 'qore-xml-module-2.3.0'
ARCHIVE = {
    'url': ('https://api.opensuse.org/public/source/home:davidnichols:qore:testing/'
            'qore-xml-module/qore-xml-module-2.3.0.tar.xz?rev=' + SOURCE_REVISION),
    'sha256': '1be5b414fec3dae283823aa8985f2d4704d538fb059842c20f692e71131aa297',
}
FIXTURES = frozenset(json.loads((Path(__file__).resolve().parents[1]
                               / 'qualification/xml-fixtures.json').read_text()))
MAX_MEMBERS = 30000
MAX_FIXTURE_BYTES = 128 * 1024 * 1024


def validate_entry(entry):
    """Changing the source pin requires reviewing the complete fixture inventory."""
    if entry.get('commit') != COMMIT or entry.get('fixtures') != []:
        raise ValueError('XML requires the reviewed archive revision and no individual fixtures')
    return ARCHIVE


def extract_fixtures(archive, destination):
    """Validate first, then atomically expose regular, unprivileged fixture files.

    Source/library directories are never extracted. No archive ownership, links,
    special files, or privileged mode bits are carried into the test directory.
    A failed extraction leaves the destination absent.
    """
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError('XML fixture destination must not exist')
    with tarfile.open(archive, 'r:*') as source:
        selected = {}
        seen = set()
        total = 0
        for count, member in enumerate(source, 1):
            if count > MAX_MEMBERS:
                raise ValueError('Too many XML archive members')
            name = member.name.rstrip('/') if member.isdir() else member.name
            path = PurePosixPath(name)
            if (not name or not path.parts or path.is_absolute() or str(path) != name or '..' in path.parts
                    or '\\' in name or '\x00' in name or path.parts[0] != ARCHIVE_ROOT):
                raise ValueError('Noncanonical XML archive member: ' + repr(member.name))
            if name in seen:
                raise ValueError('Duplicate XML archive member: ' + name)
            seen.add(name)
            relative = str(path.relative_to(ARCHIVE_ROOT))
            if relative not in FIXTURES:
                # Do not silently lose tests when the source inventory changes.
                if not member.isdir() and relative.startswith(('test/', 'docs/')):
                    raise ValueError('Unreviewed XML fixture: ' + relative)
                continue
            if not member.isfile() or member.size < 0:
                raise ValueError('XML fixtures must be regular files: ' + relative)
            total += member.size
            if total > MAX_FIXTURE_BYTES:
                raise ValueError('XML fixture archive exceeds the reviewed size limit')
            selected[relative] = member
        if set(selected) != FIXTURES:
            raise ValueError('Incomplete XML fixture archive')
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.xml-fixtures-', dir=destination.parent) as temporary:
            staged = Path(temporary) / 'source'
            staged.mkdir(mode=0o755)
            for relative, member in selected.items():
                target = staged / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.extractfile(member) as input_file, target.open('xb') as output_file:
                    shutil.copyfileobj(input_file, output_file)
                if target.stat().st_size != member.size:
                    raise ValueError('Truncated XML fixture: ' + relative)
                target.chmod(0o755 if member.mode & 0o111 else 0o644)
            staged.rename(destination)
    return {'files': len(selected), 'bytes': total,
            'suites': sum(name.startswith('test/') and name.count('/') == 1
                          and name.endswith('.qtest') for name in selected)}


def stage(directory):
    """Fetch by immutable OBS source revision, verify its hash, and stage fixtures."""
    directory = Path(directory)
    directory.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.xml-archive-', dir=directory.parent) as temporary:
        archive = Path(temporary) / 'source.tar.xz'
        fetch_source(ARCHIVE['url'], ARCHIVE['sha256'], archive)
        with archive.open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != ARCHIVE['sha256']:
                raise ValueError('XML source archive digest mismatch')
        return extract_fixtures(archive, directory)
