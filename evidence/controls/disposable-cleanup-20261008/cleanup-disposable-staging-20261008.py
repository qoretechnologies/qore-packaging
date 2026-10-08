# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Remove verified completed RPM staging and the private Go compilation cache."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / 'results/disposable-staging-cleanup-20261008.json'


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def inactive(paths):
    ids = subprocess.check_output(['docker', 'ps', '-q'], text=True).split()
    containers = json.loads(subprocess.check_output(['docker', 'inspect', *ids], text=True)) if ids else []
    for container in containers:
        for mount in container.get('Mounts', []):
            source = Path(mount['Source']).resolve()
            for path in paths:
                assert not (source == path or source.is_relative_to(path) or path.is_relative_to(source)), (container['Id'], path)
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            cwd = (process / 'cwd').resolve()
            cmdline = (process / 'cmdline').read_bytes()
            environ = (process / 'environ').read_bytes()
            descriptors = list((process / 'fd').iterdir())
            for path in paths:
                assert not cwd.is_relative_to(path), (process.name, path)
                assert str(path).encode() not in cmdline + environ, (process.name, path)
                for fd in descriptors:
                    assert not fd.resolve().is_relative_to(path), (process.name, path)
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue


candidates = json.loads((ROOT / 'results/disposable-rpm-staging-candidates-20261008.json').read_text())
rows = candidates['candidates']
assert len(rows) == 8
artifacts = {}
preserved = {}
paths = []
verified_rows = []
excluded = []
for row in rows:
    manifest = ROOT / row['manifest']
    base = manifest.parent
    state = json.loads(manifest.read_text())
    assert state['exit_code'] == 0 and len(state['artifacts']) == row['artifacts']
    local_artifacts = {}
    mismatches = []
    for name, expected in state['artifacts'].items():
        path = base / name
        assert path.resolve().is_relative_to(base.resolve())
        actual = digest(path)
        if actual != expected:
            mismatches.append({'path': str(path.relative_to(ROOT)), 'expected': expected, 'actual': actual})
        local_artifacts[str(path.relative_to(ROOT))] = expected
    if mismatches:
        excluded.append({'manifest': row['manifest'], 'reason': 'Preserved: artifact hashes do not match this historical manifest.', 'mismatches': mismatches})
        continue
    preserved[row['manifest']] = digest(manifest)
    preserved[str((base / 'build.log').relative_to(ROOT))] = digest(base / 'build.log')
    artifacts.update(local_artifacts)
    path = ROOT / row['path']
    assert path.name == 'BUILDROOT' and path.is_dir() and not path.is_symlink()
    assert path.resolve() == path and path.is_relative_to(base / 'rpmbuild')
    subprocess.run(['git', 'check-ignore', '--quiet', row['path']], cwd=ROOT, check=True)
    assert not any((ROOT / name).is_relative_to(path) for name in artifacts)
    paths.append(path)
    verified_rows.append(row)

cache = ROOT / 'work/nats-go-cache'
assert cache.is_dir() and not cache.is_symlink()
assert (cache / 'README').read_text().startswith('This directory holds cached build artifacts from the Go build system.')
cache_paths = []
for path in cache.iterdir():
    if path.name in ('README', 'trim.txt'):
        assert path.is_file() and not path.is_symlink()
    else:
        assert re.fullmatch('[0-9a-f]{2}', path.name) and path.is_dir() and not path.is_symlink(), path
        cache_paths.append(path)
assert len(cache_paths) == 256
subprocess.run(['git', 'check-ignore', '--quiet', str(cache.relative_to(ROOT))], cwd=ROOT, check=True)
inactive([*paths, cache])
cache_bytes = sum(int(subprocess.check_output(['du', '-s', '-B1', str(path)], text=True).split()[0]) for path in cache_paths)
report = {
    'schema': 1, 'date_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'authorization': 'User asked whether build artifacts could be deleted to recover filesystem space.',
    'scope': 'Verified completed RPM BUILDROOT trees and 256 private Go compiled-artifact cache buckets only.',
    'preserved': 'All RPMs, source bundles, compiled source trees, manifests, logs, evidence, images, volumes and active XML builds.',
    'staging': verified_rows, 'cache_bytes': cache_bytes,
    'artifacts_sha256': artifacts, 'manifests_and_logs_sha256': preserved,
    'excluded_invalid_manifests': candidates['excluded_invalid_manifests'],
    'excluded_unverified_artifacts': excluded,
    'free_before': shutil.disk_usage(ROOT).free, 'removed_staging': [], 'removed_cache_buckets': [],
}


def save():
    REPORT.write_text(json.dumps(report, indent=2) + '\n')


save()
for path in paths:
    inactive([path])
    shutil.rmtree(path)
    assert not path.exists()
    report['removed_staging'].append(str(path.relative_to(ROOT)))
    save()
    print('Removed', path.relative_to(ROOT), flush=True)
inactive([cache])
for path in cache_paths:
    shutil.rmtree(path)
    report['removed_cache_buckets'].append(path.name)
save()
for name, expected in {**artifacts, **preserved}.items():
    assert digest(ROOT / name) == expected, name
report.update(completed=True, bytes_removed=sum(row['bytes'] for row in verified_rows) + cache_bytes,
              free_after=shutil.disk_usage(ROOT).free)
save()
print(json.dumps({key: report[key] for key in ('bytes_removed', 'free_before', 'free_after', 'completed')}), flush=True)
