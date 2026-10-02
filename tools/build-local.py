#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Build a verified source bundle offline in an immutable container image."""
import argparse
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

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
    packaging.validate_recipe_sources((directory / manifest["spec"]).read_text(), manifest)
    return manifest


@contextmanager
def build_network(engine, internal_interface=False):
    """Provide an optional non-loopback interface without host/external routing."""
    if not internal_interface:
        yield "none", None
        return
    if engine != "docker":
        raise ValueError("The isolated internal interface requires Docker")
    name = "qore-rpm-isolated-" + uuid.uuid4().hex
    options = {"com.docker.network.bridge.gateway_mode_ipv4": "isolated",
               "com.docker.network.bridge.gateway_mode_ipv6": "isolated"}
    command = [engine, "network", "create", "--driver", "bridge", "--internal"]
    for key, value in options.items():
        command.extend(["--opt", key + "=" + value])
    created = subprocess.check_output([*command, name], text=True).strip()
    try:
        if not re.fullmatch(r"[a-f0-9]{64}", created):
            raise ValueError("Expected an immutable network ID")
        info = json.loads(subprocess.check_output([engine, "network", "inspect", created], text=True))[0]
        if (info.get("Id") != created or info.get("Name") != name or info.get("Driver") != "bridge"
                or info.get("Internal") is not True or info.get("Containers")
                or any(info.get("Options", {}).get(k) != v for k, v in options.items())):
            raise ValueError("Build network is not an empty isolated internal bridge")
        yield created, info
    finally:
        subprocess.run([engine, "network", "rm", name], check=True, stdout=subprocess.DEVNULL)


def build(source, image, output, jobs=2, engine="docker", source_only=False, internal_interface=False):
    manifest = verify_bundle(source)
    if jobs < 1 or jobs > 16:
        raise ValueError("Use between 1 and 16 build jobs")
    if internal_interface and engine != "docker":
        raise ValueError("The isolated internal interface requires Docker")
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
    with build_network(engine, internal_interface) as (network, network_info):
        command[command.index("--network") + 1] = network
        record["network"] = "isolated-bridge" if internal_interface else "none"
        if network_info is not None:
            record["network_info"] = network_info
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


def launch_background(source, image, output, jobs=2, engine="docker", source_only=False,
                      internal_interface=False):
    """Keep the driver and its completion record alive across terminal closure."""
    verify_bundle(source)
    if jobs < 1 or jobs > 16:
        raise ValueError("Use between 1 and 16 build jobs")
    if internal_interface and engine != "docker":
        raise ValueError("The isolated internal interface requires Docker")
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError("Use a new build output directory")
    info = json.loads(subprocess.check_output([engine, "image", "inspect", image], text=True))[0]
    image_id = info["Id"]
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", image_id):
        raise ValueError("Expected an immutable image ID")
    command = [sys.executable, str(Path(__file__).resolve()), "--source", str(source),
               "--image", image_id, "--output", str(output), "--jobs", str(jobs), "--engine", engine]
    if source_only:
        command.append("--source-only")
    if internal_interface:
        command.append("--internal-interface")
    output.parent.mkdir(parents=True, exist_ok=True)
    driver_log = output.with_name(output.name + "-driver.log")
    # Exclusive creation prevents launching a second driver for this output.
    # The child inherits an open regular file, never the interactive tool pipe.
    with driver_log.open("x") as log:
        actions = [(os.POSIX_SPAWN_OPEN, 0, os.devnull, os.O_RDONLY, 0),
                   (os.POSIX_SPAWN_DUP2, log.fileno(), 1),
                   (os.POSIX_SPAWN_DUP2, log.fileno(), 2),
                   (os.POSIX_SPAWN_CLOSE, log.fileno())]
        pid = os.posix_spawn(sys.executable, command, os.environ.copy(),
                             file_actions=actions, setsid=True)
    return {"pid": pid, "image": image_id, "output": str(output),
            "driver_log": str(driver_log), "status": "launched; build.json records completion"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--image", required=True, help="prepared build-dependency image; its immutable ID is recorded")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--engine", choices=("docker", "podman"), default="docker")
    parser.add_argument("--source-only", action="store_true")
    parser.add_argument("--internal-interface", action="store_true",
                        help="Docker only: private internal bridge for tests requiring a non-loopback interface")
    parser.add_argument("--background", action="store_true",
                        help="launch a persistent driver; read build.json for the final result")
    args = parser.parse_args()
    if args.background:
        print(json.dumps(launch_background(args.source, args.image, args.output, args.jobs,
                                           args.engine, args.source_only, args.internal_interface), indent=2))
        return
    sys.exit(build(args.source, args.image, args.output, args.jobs, args.engine, args.source_only,
                   args.internal_interface))


if __name__ == "__main__":
    main()
