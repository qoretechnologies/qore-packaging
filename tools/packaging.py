#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Reproducible source preparation and inventory for Qore's RPM packages."""

import argparse
import hashlib
import io
import json
import os
import posixpath
import re
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], stderr=subprocess.PIPE)


def build_order(packages):
    """Topological order; missing prerequisites and cycles are errors."""
    pending = {name: set(info["build_after"]) for name, info in packages.items()}
    unknown = set().union(*pending.values()) - pending.keys() if pending else set()
    if unknown:
        raise ValueError("Unknown prerequisites: " + ", ".join(sorted(unknown)))
    result = []
    while pending:
        ready = sorted(name for name, deps in pending.items() if not deps)
        if not ready:
            raise ValueError("Dependency cycle: " + ", ".join(sorted(pending)))
        for name in ready:
            del pending[name]
            result.append(name)
        for deps in pending.values():
            deps.difference_update(ready)
    return result


def prepare_source(repo, ref, name, version, output, exclusions=(), packaging_overlay=None, spec_path=None,
                   vendor_manifest=None, cache=None):
    """Archive exactly one commit; normalize ownership, ordering and timestamps.

    No checkout or ignored build outputs are read. Required vendored sources
    are separate, checksum-verified Source entries, never download-cache state.
    """
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9+._-]*", name):
        raise ValueError("Invalid package name")
    if not re.fullmatch(r"[0-9][a-zA-Z0-9+._~]*", version):
        raise ValueError("Invalid RPM version")
    output = Path(output)
    if output.exists():
        raise ValueError("Output directory must not exist")
    if bool(vendor_manifest) != (cache is not None):
        raise ValueError("Vendor manifest and source cache must be supplied together")
    commit = git(repo, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()
    timestamp = int(git(repo, "show", "-s", "--format=%ct", commit).decode())
    archive = git(repo, "archive", "--format=tar", commit)
    prefix = f"{name}-{version}"
    overlays = {}
    if packaging_overlay is not None:
        overlay_root = Path(packaging_overlay)
        paths = list(overlay_root.glob("*.spec*")) + list((overlay_root / "rpm").rglob("*"))
        for path in paths:
            if path.is_dir() or "__pycache__" in path.parts:
                continue
            relative = path.relative_to(overlay_root).as_posix()
            if path.is_symlink():
                raise ValueError("Candidate overlays must contain regular files, not symlinks")
            overlays[relative] = path
    recipe = None
    if spec_path is not None:
        if spec_path.startswith("/") or ".." in Path(spec_path).parts:
            raise ValueError("Spec path must be inside the repository")
        recipe = (overlays[spec_path].read_text() if spec_path in overlays
                  else git(repo, "show", commit + ":" + spec_path).decode())
        names = re.findall(r"^Name:\s+(\S+)\s*$", recipe, flags=re.M)
        if names != [name]:
            raise ValueError("Spec name does not match the archive name")
        recipe, count = re.subn(r"^Version:[^\n]+", "Version: " + version, recipe, flags=re.M)
        if count != 1:
            raise ValueError("Expected one explicit Version in the spec")
    # Construct everything in memory before creating the destination. A failed
    # Git command or invalid archive must not leave a plausible release upload.
    compressed = io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(archive)) as source:
        with tarfile.open(fileobj=compressed, mode="w:xz", format=tarfile.PAX_FORMAT) as target:
            for member in sorted(source.getmembers(), key=lambda entry: entry.name):
                path = member.name.rstrip("/")
                if path in overlays:
                    continue
                if any(path == value or path.startswith(value + "/") for value in exclusions):
                    continue
                if not (member.isfile() or member.isdir() or member.issym()):
                    raise ValueError(f"Unsupported source archive entry: {path}")
                if path.startswith("/") or ".." in Path(path).parts:
                    raise ValueError(f"Unsafe archive path: {path}")
                if member.issym():
                    destination = posixpath.normpath(posixpath.join(posixpath.dirname(path), member.linkname))
                    if destination.startswith(("/", "../")) or destination == "..":
                        raise ValueError(f"Source symlink escapes archive: {path}")
                member.name = prefix + "/" + path
                member.uid = member.gid = 0
                member.uname = member.gname = "root"
                member.mtime = timestamp
                member.pax_headers = {}
                target.addfile(member, source.extractfile(member) if member.isfile() else None)
            for relative, path in sorted(overlays.items()):
                data = path.read_bytes()
                member = tarfile.TarInfo(prefix + "/" + relative)
                member.size, member.mtime = len(data), timestamp
                member.uid = member.gid = 0
                member.uname = member.gname = "root"
                member.mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
                target.addfile(member, io.BytesIO(data))
    payload = compressed.getvalue()
    filename = prefix + ".tar.xz"
    manifest = {"schema": 1, "commit": commit, "source_date_epoch": timestamp,
                "name": name, "version": version, "exclusions": list(exclusions),
                "sources": {filename: hashlib.sha256(payload).hexdigest()}}
    if packaging_overlay is not None:
        manifest["candidate"] = True
        manifest["packaging_overlay"] = {name: hashlib.sha256(path.read_bytes()).hexdigest()
                                          for name, path in sorted(overlays.items())}
    if recipe is not None:
        manifest["spec"] = name + ".spec"
        manifest["sources"][name + ".spec"] = hashlib.sha256(recipe.encode()).hexdigest()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".qore-source-", dir=output.parent) as temporary:
        staging = Path(temporary) / "ready"
        staging.mkdir()
        (staging / filename).write_bytes(payload)
        if recipe is not None:
            (staging / (name + ".spec")).write_text(recipe)
        if vendor_manifest:
            components = prepare_components(repo, commit, vendor_manifest, overlays, cache,
                                            staging, timestamp, set(manifest["sources"]))
            manifest["vendor_manifest"] = vendor_manifest
            manifest["components"] = components
            for component in components:
                path = staging / component["archive"]
                with path.open("rb") as stream:
                    manifest["sources"][path.name] = hashlib.file_digest(stream, "sha256").hexdigest()
        (staging / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        # mkdir reserves the destination exclusively; replace only our empty
        # reservation, never a caller's already existing directory.
        output.mkdir(exist_ok=False)
        try:
            os.replace(staging, output)
        except BaseException:
            output.rmdir()
            raise
    return manifest


def prepare_components(repo, commit, manifest_path, overlays, cache, staging, timestamp, reserved):
    """Read committed pins and produce normalized, licensed vendor archives."""
    path = Path(manifest_path)
    if path.is_absolute() or any(part in ("..", ".") for part in path.parts):
        raise ValueError("Vendor manifest must be inside the repository")
    data = (overlays[manifest_path].read_bytes() if manifest_path in overlays
            else git(repo, "show", commit + ":" + manifest_path))
    config = json.loads(data)
    components = config.get("components") if isinstance(config, dict) else None
    if not isinstance(config, dict) or config.get("schema") != 1 or not isinstance(components, list) or not components:
        raise ValueError("Vendor manifest needs schema 1 and nonempty components")
    names = set(reserved) | {"source-manifest.json"}
    for component in components:
        if not isinstance(component, dict):
            raise ValueError("Vendor components must be objects")
        archive = component.get("archive", "")
        if not isinstance(archive, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*\.tar\.xz", archive) or archive in names:
            raise ValueError("Vendor archives must have unique safe tar.xz names")
        names.add(archive)
        top = component.get("top", "")
        if not isinstance(top, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", top):
            raise ValueError("Invalid component archive root")
        url = component.get("url", "")
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ValueError("Source downloads require HTTPS")
        if not isinstance(component.get("licenses"), list) or not component["licenses"]:
            raise ValueError("Vendor components must name their retained license files")
        for field in ("licenses", "excluded", "retained_paths"):
            values = component.get(field, [])
            if not isinstance(values, list) or any(
                    not isinstance(value, str) or not value or value.startswith("/")
                    or any(part in ("", ".", "..") for part in value.split("/")) for value in values):
                raise ValueError("Vendor paths must be safe relative paths")
        digest = component.get("sha256", "")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Expected a lowercase SHA-256 digest")
    for component in components:
        digest = component["sha256"]
        downloaded = fetch_source(component["url"], digest, Path(cache) / digest)
        destination = staging / component["archive"]
        repack_component(downloaded, digest, component["top"], timestamp, destination,
                         component.get("excluded", []), component.get("retained_paths", []))
        with tarfile.open(destination) as archive:
            for license_path in component["licenses"]:
                name = component["top"] + "/" + license_path
                try:
                    member = archive.getmember(name)
                except KeyError as error:
                    raise ValueError("Vendor license was not retained: " + name) from error
                if not member.isfile() or member.size == 0:
                    raise ValueError("Vendor license must be a nonempty file: " + name)
    return components


def verify_download(path, digest):
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Expected a lowercase SHA-256 digest")
    with Path(path).open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != digest:
        raise ValueError(f"Source checksum mismatch: {Path(path).name}")


def fetch_source(url, digest, destination):
    """Fetch a pinned upstream source; never expose an unverified cache entry."""
    destination = Path(destination)
    if destination.exists():
        verify_download(destination, digest)
        return destination
    if not url.startswith("https://"):
        raise ValueError("Source downloads require HTTPS")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".download-", dir=destination.parent) as tmp:
        candidate = Path(tmp) / "source"
        with urllib.request.urlopen(url, timeout=60) as response, candidate.open("xb") as stream:
            while block := response.read(1024 * 1024):
                stream.write(block)
        verify_download(candidate, digest)
        # An exclusive hard link also handles concurrent downloaders safely.
        try:
            os.link(candidate, destination)
        except FileExistsError:
            verify_download(destination, digest)
    return destination


def repack_component(source, digest, top, timestamp, destination, exclusions=(), retained=()):
    """Normalize a verified vendor tarball and omit explicitly excluded fixtures."""
    verify_download(source, digest)
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._+-]*", top):
        raise ValueError("Invalid component archive root")
    destination = Path(destination)
    if destination.exists():
        raise ValueError("Component output already exists")
    payload = io.BytesIO()
    with tarfile.open(source) as original, tarfile.open(fileobj=payload, mode="w:xz") as result:
        for member in sorted(original.getmembers(), key=lambda entry: entry.name):
            parts = Path(member.name).parts
            if not parts or parts[0] != top or ".." in parts or member.name.startswith("/"):
                raise ValueError("Unsafe component archive path: " + member.name)
            relative = "/".join(parts[1:])
            if any(relative == p or relative.startswith(p + "/") for p in exclusions):
                continue
            if retained and relative and not any(
                    relative == p or relative.startswith(p + "/") or p.startswith(relative + "/")
                    for p in retained):
                continue
            if not (member.isfile() or member.isdir()):
                raise ValueError("Unsupported component archive entry: " + member.name)
            member.uid = member.gid = 0
            member.uname = member.gname = "root"
            member.mtime = timestamp
            member.pax_headers = {}
            result.addfile(member, original.extractfile(member) if member.isfile() else None)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".repack-", dir=destination.parent) as tmp:
        candidate = Path(tmp) / "source"
        candidate.write_bytes(payload.getvalue())
        os.link(candidate, destination)
    return hashlib.sha256(payload.getvalue()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("order", help="print the catalog's dependency build order")
    prepare = commands.add_parser("prepare", help="prepare a clean source archive")
    prepare.add_argument("--repo", type=Path, required=True)
    prepare.add_argument("--ref", required=True)
    prepare.add_argument("--name", required=True)
    prepare.add_argument("--version", required=True)
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--exclude", action="append", default=[])
    prepare.add_argument("--packaging-overlay", type=Path,
                         help="candidate builds only: overlay rpm/ and spec files, recording every digest")
    prepare.add_argument("--spec", help="repository-relative canonical spec path")
    prepare.add_argument("--vendor-manifest", help="repository-relative RPM vendor manifest, read from the same commit")
    prepare.add_argument("--cache", type=Path, help="checksum-addressed upstream source cache")
    args = parser.parse_args()
    if args.command == "order":
        print("\n".join(build_order(json.loads((ROOT / "catalog.json").read_text())["packages"])))
    else:
        print(json.dumps(prepare_source(args.repo, args.ref, args.name, args.version,
                                        args.output, args.exclude, args.packaging_overlay, args.spec,
                                        args.vendor_manifest, args.cache), indent=2))


if __name__ == "__main__":
    main()
