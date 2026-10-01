#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Prepare and apply explicit OBS project/source operations with osc."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET

loader = importlib.util.spec_from_file_location("build_local", Path(__file__).with_name("build-local.py"))
builder = importlib.util.module_from_spec(loader)
loader.loader.exec_module(builder)
API = "https://api.opensuse.org"
PREFIX = "home:davidnichols:qore:"


def osc(*args, **kwargs):
    # osc's streamfile counts the initial download as an attempt. Zero prevents
    # every checkout download before HTTP is called; one permits that request.
    return subprocess.run(["osc", "--setopt", "http_retries=1", "-A", API, *args],
                          check=True, **kwargs)


def validate_project(path):
    root = ET.parse(path).getroot()
    project = root.get("name", "")
    if root.tag != "project" or project not in (PREFIX + "testing", PREFIX + "stable"):
        raise ValueError("Only the Qore testing/stable subprojects are managed")
    maintainers = [p.get("userid") for p in root.findall("person") if p.get("role") == "maintainer"]
    if "davidnichols" not in maintainers:
        raise ValueError("The project owner must remain a maintainer")
    for flag in ("build", "publish"):
        setting = root.find(flag)
        if setting is None or [c.tag for c in setting] != ["disable"] or setting[0].attrib:
            raise ValueError("New projects must start with builds and publication disabled")
    return project


def validate_upload(project, source):
    if project != PREFIX + "testing":
        raise ValueError("Direct source uploads are restricted to testing; stable requires promotion")
    manifest = builder.verify_bundle(source)
    if manifest.get("candidate") or manifest.get("packaging_overlay"):
        raise ValueError("Commit and re-prepare candidate packaging before an OBS upload")
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9+._-]*", manifest.get("name", "")):
        raise ValueError("Invalid source package name")
    if not re.fullmatch(r"[a-f0-9]{40}", manifest.get("commit", "")):
        raise ValueError("Uploads require a pinned packaging/source commit")
    return manifest


def create_project(metadata, apply):
    project = validate_project(metadata)
    # First list the parent as an authenticated permission/connectivity check.
    osc("api", "/source/home:davidnichols/_meta", stdout=subprocess.DEVNULL)
    result = subprocess.run(["osc", "--setopt", "http_retries=1", "-A", API,
                             "api", f"/source/{project}/_meta"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode == 0:
        raise ValueError("Project already exists; review its metadata before changing it")
    if "404" not in result.stderr:
        raise RuntimeError(result.stderr.strip())
    print(f"Create {project} from {metadata}; builds and publication disabled")
    if apply:
        osc("api", "-X", "PUT", "-T", str(metadata), f"/source/{project}/_meta")


def upload(project, source, apply):
    source = Path(source).resolve()
    manifest = validate_upload(project, source)
    package = manifest["name"]
    print(json.dumps({"project": project, "package": package, "commit": manifest["commit"],
                      "sources": manifest["sources"]}, indent=2))
    if not apply:
        return
    # This never creates a replacement package silently. Initialize its metadata
    # explicitly first, then use an ordinary checked-out osc working copy.
    osc("api", f"/source/{project}/{package}/_meta", stdout=subprocess.DEVNULL)
    with tempfile.TemporaryDirectory(prefix="qore-obs-upload-") as tmp:
        working = Path(tmp) / "package"
        osc("checkout", "--output-dir", str(working), project, package)
        old_names = {p.name for p in working.iterdir() if p.name != ".osc"}
        expected = set(manifest["sources"]) | {"source-manifest.json"}
        unexpected = old_names - expected
        removable = set()
        if unexpected and (working / "source-manifest.json").is_file():
            previous = builder.verify_bundle(working)
            removable = unexpected & set(previous["sources"])
        unmanaged = unexpected - removable
        # Service/link/patch files outside a verified previous bundle can change
        # the build; preserve and report them. Normal versioned archive upgrades
        # remove only files managed by the previous verified manifest.
        if unmanaged:
            raise ValueError("Unexpected existing OBS sources: " + ", ".join(sorted(unmanaged)))
        for name in sorted(removable):
            osc("remove", name, cwd=working)
        for name in sorted(expected):
            (working / name).write_bytes((source / name).read_bytes())
        osc("addremove", cwd=working)
        osc("commit", "-m", "Pinned source " + manifest["commit"], cwd=working)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    project = commands.add_parser("create-project")
    project.add_argument("metadata", type=Path)
    project.add_argument("--apply", action="store_true")
    source = commands.add_parser("upload")
    source.add_argument("--project", required=True)
    source.add_argument("--source", type=Path, required=True)
    source.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.command == "create-project":
        create_project(args.metadata, args.apply)
    else:
        upload(args.project, args.source, args.apply)


if __name__ == "__main__":
    main()
