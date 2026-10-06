#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Prepare a backport source bundle from pinned upstream and packaging inputs."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import tempfile

loader = importlib.util.spec_from_file_location("packaging", Path(__file__).with_name("packaging.py"))
packaging = importlib.util.module_from_spec(loader)
loader.loader.exec_module(packaging)


def prepare(repo, name, cache, output, ref=None, candidate=False):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9+._-]*", name):
        raise ValueError("Invalid dependency name")
    if candidate == bool(ref):
        raise ValueError("Choose exactly one of a committed ref or a candidate working tree")
    repo, cache, output = Path(repo), Path(cache), Path(output)
    if output.exists():
        raise ValueError("Output directory must not exist")
    commit = None if candidate else packaging.git(
        repo, "rev-parse", "--verify", "--end-of-options", ref + "^{commit}").decode().strip()

    def read(relative):
        if commit:
            return packaging.git(repo, "show", commit + ":dependencies/" + relative)
        path = repo / "dependencies" / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError("Packaging inputs must be regular files")
        return path.read_bytes()

    info = json.loads(read("sources.json"))[name]
    archives = [info, *info.get("components", [])]
    names = [name + ".spec", *(entry["archive"] for entry in archives), *info.get("extra_sources", [])]
    if len(names) != len(set(names)) or any(
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9+._-]*", entry) for entry in names):
        raise ValueError("Source filenames must be unique safe basenames")
    archive_names = {entry["archive"] for entry in archives}
    payloads = {entry: read(entry) for entry in names if entry not in archive_names}
    for entry in archives:
        archive = cache / entry["archive"]
        if archive.is_symlink() or not archive.is_file():
            raise ValueError("Download the pinned archive into the cache first")
        packaging.verify_download(archive, entry["sha256"])
        data = archive.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("Source archive changed while preparing the bundle")
        payloads[entry["archive"]] = data
    recipe = payloads[name + ".spec"].decode()
    preamble, _ = packaging.split_spec_preamble(recipe)
    for field, value in (("Name", name), ("Version", info["version"])):
        if re.findall(r"^" + field + r":\s+(\S+)\s*$", preamble, re.M) != [value]:
            raise ValueError("Dependency spec and source pin disagree: " + field)
    timestamp = info["source_date_epoch"] if candidate else int(
        packaging.git(repo, "show", "-s", "--format=%ct", commit).decode())
    if type(timestamp) is not int or timestamp < 0:
        raise ValueError("Invalid dependency timestamp")
    changes = packaging.obs_changelog(recipe)
    if changes is not None:
        filename = name + ".changes"
        if filename in payloads and payloads[filename] != changes.encode():
            raise ValueError("Existing OBS changelog disagrees with the RPM recipe")
        payloads[filename] = changes.encode()
    manifest = {"schema": 1, "name": name, "version": info["version"], "commit": commit,
                "source_date_epoch": timestamp, "spec": name + ".spec",
                "upstream": {"url": info["url"], "sha256": info["sha256"]},
                "sources": {entry: hashlib.sha256(data).hexdigest() for entry, data in sorted(payloads.items())}}
    if candidate:
        manifest["candidate"] = True
    if info.get("components"):
        manifest["components"] = info["components"]
    packaging.validate_recipe_sources(recipe, manifest)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".dependency-", dir=output.parent) as tmp:
        staging = Path(tmp) / "ready"
        staging.mkdir()
        for entry, data in payloads.items():
            (staging / entry).write_bytes(data)
        (staging / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        output.mkdir(exist_ok=False)
        try:
            os.replace(staging, output)
        except BaseException:
            output.rmdir()
            raise
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--name", required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--ref")
    selection.add_argument("--candidate", action="store_true")
    args = parser.parse_args()
    print(json.dumps(prepare(args.repo, args.name, args.cache, args.output, args.ref, args.candidate), indent=2))


if __name__ == "__main__":
    main()
