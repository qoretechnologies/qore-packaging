#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Exercise the real foreground and detached Docker/RPM temporary volume."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile

loader = importlib.util.spec_from_file_location(
    'builder', Path(__file__).resolve().parents[1] / 'tools/build-local.py')
builder = importlib.util.module_from_spec(loader)
loader.loader.exec_module(builder)

SPEC = '''Name: qore-rpm-tmpfs-probe
Version: 1
Release: 1
Summary: Private temporary filesystem qualification fixture
License: MIT
BuildArch: noarch
Source0: probe.py
%description
Private qualification fixture for isolated test filesystem capacity.
%prep
%build
%install
install -Dm644 %{SOURCE0} %{buildroot}%{_datadir}/qore-rpm-tmpfs-probe/probe.py
%check
python3 -B -W error %{SOURCE0}
%files
%{_datadir}/qore-rpm-tmpfs-probe
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--background', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='qore-tmpfs-probe-') as temporary:
        source = Path(temporary)
        (source / 'probe.py').write_bytes((Path(__file__).with_name('fixtures') / 'tmpfs_probe.py').read_bytes())
        (source / 'probe.spec').write_text(SPEC)
        manifest = {'schema': 1, 'spec': 'probe.spec', 'source_date_epoch': 1767225600,
                    'sources': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source.iterdir()}}
        (source / 'source-manifest.json').write_text(json.dumps(manifest))
        if args.background:
            launched = builder.launch_background(source, args.image, args.output, tmpfs_mib=128)
            _, status = os.waitpid(launched['pid'], 0)
            assert os.waitstatus_to_exitcode(status) == 0
        else:
            assert builder.build(source, args.image, args.output, tmpfs_mib=128) == 0
    record = json.loads((args.output / 'build.json').read_text())
    assert record['exit_code'] == 0 and record['artifacts'] and record['tmpfs_mib'] == 128
    assert 'PASS: bounded private /tmp' in (args.output / 'build.log').read_text()
    print('PASS:', args.output)


if __name__ == '__main__':
    main()
