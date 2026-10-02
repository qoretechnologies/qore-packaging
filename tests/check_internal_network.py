#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Run the Docker/RPM integration test for an isolated build interface."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile

loader = importlib.util.spec_from_file_location(
    "builder", Path(__file__).resolve().parents[1] / "tools/build-local.py")
builder = importlib.util.module_from_spec(loader)
loader.loader.exec_module(builder)

SPEC = """Name: qore-rpm-network-probe
Version: 1
Release: 1
Summary: Private offline network qualification fixture
License: MIT
BuildArch: noarch
Source0: probe.py
%description
Private qualification fixture for the isolated build interface.
%prep
%build
%install
install -Dm644 %{SOURCE0} %{buildroot}%{_datadir}/qore-rpm-network-probe/probe.py
%check
python3 -B -W error %{SOURCE0}
%files
%{_datadir}/qore-rpm-network-probe
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="qore-network-probe-") as temporary:
        source = Path(temporary)
        probe = (Path(__file__).with_name("fixtures") / "internal_network_probe.py").read_bytes()
        (source / "probe.py").write_bytes(probe)
        (source / "probe.spec").write_text(SPEC)
        manifest = {
            "schema": 1, "spec": "probe.spec", "source_date_epoch": 1767225600,
            "sources": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir()},
        }
        (source / "source-manifest.json").write_text(json.dumps(manifest))
        assert builder.build(source, args.image, args.output, internal_interface=True) == 0
    record = json.loads((args.output / "build.json").read_text())
    assert record["network"] == "isolated-bridge" and record["artifacts"]
    result = subprocess.run(["docker", "network", "inspect", record["network_info"]["Id"]],
                            capture_output=True, text=True)
    assert result.returncode and "not found" in result.stderr, result.stderr
    args.output.with_name(args.output.name + "-qualification.json").write_text(
        json.dumps({"exit_code": 0, "network_removed": True, "build": record}, indent=2) + "\n")


if __name__ == "__main__":
    main()
