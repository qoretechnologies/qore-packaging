#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Build a verified source bundle offline in an immutable container image."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

loader = importlib.util.spec_from_file_location("qore_packaging", Path(__file__).with_name("packaging.py"))
packaging = importlib.util.module_from_spec(loader)
loader.loader.exec_module(packaging)


def verify_bundle(directory):
    directory = Path(directory)
    manifest = json.loads((directory / "source-manifest.json").read_text())
    if manifest.get("schema") != 1 or not manifest.get("sources"):
        raise ValueError("Unsupported or empty source manifest")
    if not re.fullmatch(r"[A-Za-z0-9._+-]+\.spec", manifest.get("spec", "")):
        raise ValueError("Manifest must identify a spec file")
    if manifest["spec"] not in manifest["sources"]:
        raise ValueError("Spec checksum is missing")
    if not isinstance(manifest.get("source_date_epoch"), int) or manifest["source_date_epoch"] < 0:
        raise ValueError("Invalid source timestamp")
    for name, digest in manifest["sources"].items():
        if Path(name).name != name or name in (".", ".."):
            raise ValueError("Manifest source names must be basenames")
        source = directory / name
        if source.is_symlink() or not source.is_file():
            raise ValueError("Manifest sources must be regular files")
        packaging.verify_download(source, digest)
    return manifest


def build(source, image, output, jobs=2, engine="docker", source_only=False):
    manifest = verify_bundle(source)
    if jobs < 1 or jobs > 16:
        raise ValueError("Use between 1 and 16 build jobs")
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("Use a new build output directory")
    image_info = json.loads(subprocess.check_output([engine, "image", "inspect", image], text=True))[0]
    image_id = image_info["Id"]
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", image_id):
        raise ValueError("Expected an immutable image ID")
    # There is no shell interpolation of caller-controlled paths or arguments.
    script = """set -eu
mkdir -p /work/home /work/rpmbuild
rpm -qa --qf '%{NAME} %{EPOCHNUM}:%{VERSION}-%{RELEASE}.%{ARCH}\\n' | sort > /work/installed-packages.txt
exec rpmbuild "$@"
"""
    output.mkdir(parents=True, exist_ok=False)
    # rpmbuild is not an init process: interrupted process-tree tests leave
    # orphaned grandchildren that PID 1 must reap, just as on the target OS.
    command = [engine, "run", "--rm", "--init", "--network", "none", "--hostname", "qore-rpm-builder",
               "--user", f"{os.getuid()}:{os.getgid()}", "-e", "HOME=/work/home",
               "-e", f"SOURCE_DATE_EPOCH={manifest['source_date_epoch']}",
               "-v", f"{source}:/sources:ro", "-v", f"{output}:/work", image_id,
               "sh", "-c", script, "build-local", "-bs" if source_only else "-ba",
               "--define", "_topdir /work/rpmbuild", "--define", "_sourcedir /sources",
               "--define", f"_smp_build_ncpus {jobs}", "--define", "_buildhost qore-rpm-builder",
               "/sources/" + manifest["spec"]]
    record = {"schema": 1, "image": image_id, "source": manifest, "jobs": jobs,
              "network": "none", "command": command, "source_only": source_only}
    (output / "build.json").write_text(json.dumps(record, indent=2) + "\n")
    with (output / "build.log").open("w") as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    record["exit_code"] = result.returncode
    record["artifacts"] = {}
    for path in sorted(output.rglob("*.rpm")):
        with path.open("rb") as stream:
            record["artifacts"][str(path.relative_to(output))] = hashlib.file_digest(stream, "sha256").hexdigest()
    (output / "build.json").write_text(json.dumps(record, indent=2) + "\n")
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--image", required=True, help="prepared build-dependency image; its immutable ID is recorded")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--engine", choices=("docker", "podman"), default="docker")
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args()
    sys.exit(build(args.source, args.image, args.output, args.jobs, args.engine, args.source_only))


if __name__ == "__main__":
    main()
