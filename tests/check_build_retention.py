#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Check RPM build retention and normal cleanup with a real container image."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re

loader = importlib.util.spec_from_file_location(
    "builder", Path(__file__).resolve().parents[1] / "tools/build-local.py")
builder = importlib.util.module_from_spec(loader)
loader.loader.exec_module(builder)

SPEC = """Name: qore-rpm-retention-probe
Version: 1
Release: 1
Summary: RPM build retention qualification fixture
License: MIT
URL: https://qore.org/
BuildArch: noarch
%description
Private qualification fixture for retaining native diagnostic binaries.
%prep
%setup -q -T -c -n qore-rpm-retention-probe-1
%build
printf 'retained build data\n' > retention-marker
%install
install -Dm644 retention-marker %{buildroot}%{_datadir}/qore-rpm-retention-probe/data
%check
cmp retention-marker %{buildroot}%{_datadir}/qore-rpm-retention-probe/data
echo 'RETENTION_CHECK_PASSED'
%clean
test -f retention-marker
mv retention-marker cleaned-marker
echo 'RETENTION_CLEAN_EXECUTED'
%files
%{_datadir}/qore-rpm-retention-probe
%changelog
* Wed Oct 07 2026 Qore Technologies <info@qoretechnologies.com> - 1-1
- Qualify optional build retention.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = args.output / "source"
    source.mkdir()
    (source / "probe.spec").write_text(SPEC)
    manifest = {"schema": 1, "spec": "probe.spec", "source_date_epoch": 1791331200,
                "sources": {"probe.spec": hashlib.sha256(SPEC.encode()).hexdigest()}}
    (source / "source-manifest.json").write_text(json.dumps(manifest))
    records = []
    for background in (False, True):
        for keep in (False, True):
            output = args.output / f"background-{background}-retain-{keep}"
            if background:
                launched = builder.launch_background(source, args.image, output, keep_build=keep)
                _, status = os.waitpid(launched["pid"], 0)
                assert os.waitstatus_to_exitcode(status) == 0, output
            else:
                assert builder.build(source, args.image, output, keep_build=keep) == 0, output
            record = json.loads((output / "build.json").read_text())
            assert record["exit_code"] == 0 and record["artifacts"], output
            assert record["keep_build"] == keep, output
            log = (output / "build.log").read_text()
            assert "RETENTION_CHECK_PASSED" in log, output
            assert ("RETENTION_CLEAN_EXECUTED" in log) == (not keep), output
            assert not re.search(r"(?:warning:|error:)", log, re.I), output
            markers = list((output / "rpmbuild/BUILD").rglob("retention-marker"))
            assert len(markers) == int(keep), (output, markers)
            if keep:
                assert markers[0].read_text() == "retained build data\n", output
            records.append({"background": background, "keep_build": keep, "passed": True})
    (args.output / "status.json").write_text(json.dumps(records, indent=2) + "\n")
    print("PASS: all four foreground/background retention and cleanup checks", args.output)


if __name__ == "__main__":
    main()
