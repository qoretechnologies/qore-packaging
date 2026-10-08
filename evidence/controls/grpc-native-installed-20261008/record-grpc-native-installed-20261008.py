# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import shutil

root = Path.cwd()
out = root / 'evidence/controls/grpc-native-installed-20261008'
out.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
records = {}
for target, job in [('fedora', 209791), ('leap', 209792), ('el10', 209793)]:
    source = root / f'results/grpc-installed-native-20261008/{target}'
    base = source / 'results/native-installed'
    result = json.loads((base / 'qualification.json').read_text())
    detail = json.loads((source / 'job.json').read_text())
    assert detail['status'] == 'success' and detail['pipeline']['id'] == 60033
    assert detail['commit']['id'] == '5f1d419ef9f0ec678b1e64f80511e97c7876c13f'
    assert result['machine'] == 'aarch64' and result['exit_code'] == 0
    assert all(s['exit_code'] == 0 for s in result['steps'])
    assert result['manifest'] == json.loads((root / f'qualification/grpc-{target}-aarch64.json').read_text())
    phases = {}
    for phase in ['runtime', 'sdk']:
        suites = {}
        for p in sorted(base.glob(phase + '-grpc-*.log')):
            counts = [tuple(map(int, m)) for m in re.findall(r'Ran (\d+) test cases, (\d+) succeeded \((\d+) assertions\)', p.read_text())]
            if not counts:
                continue
            assert len(counts) == 1 and counts[0][0] == counts[0][1]
            suites[p.stem.removeprefix(phase + '-grpc-')] = {'cases': counts[0][0], 'assertions': counts[0][2]}
        assert len(suites) == 13
        assert sum(c['cases'] for c in suites.values()) == 379
        assert sum(c['assertions'] for c in suites.values()) == 1790
        phases[phase] = suites
    steps = {s['name'] for s in result['steps']}
    assert {'runtime-runtime', 'sdk-runtime', 'sdk-development', 'sdk-tools', 'sdk-remote-debuggers', 'sdk-grpc-compiler'} <= steps
    signatures = [s for s in steps if s.startswith('verify-signature-')]
    assert len(signatures) == {'fedora': 14, 'leap': 28, 'el10': 17}[target]
    records[target] = {'pipeline': 60033, 'job': job, 'steps': len(steps), 'verified_signatures': len(signatures), 'phases': phases}
    for p in sorted(source.rglob('*')):
        if not p.is_file():
            continue
        dest = out / target / (p.relative_to(base) if p.is_relative_to(base) else p.relative_to(source))
        dest.parent.mkdir(parents=True, exist_ok=True)
        if p.suffix == '.log':
            dest.with_suffix('.log.gz').write_bytes(gzip.compress(p.read_bytes(), mtime=0))
        else:
            shutil.copyfile(p, dest)
control = root / 'results/grpc-connect-aot-control-20261008.log'
text = control.read_text()
assert text.count('warning:') == 1 and 'Connect.qm"\n"/usr/lib64/qore-modules/3.0.0/Connect/Connect.qmod"' in text
shutil.copyfile(control, out / control.name)
for name in ['record-grpc-native-installed-20261008.py', 'download-grpc-installed-20261008.py']:
    shutil.copyfile(root / 'work' / name, out / name)
evidence = {
 'schema': 1, 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.', 'date': '2026-10-08',
 'result': 'All signed native ARM runtime/SDK functional checks pass; exact Connect source-fallback diagnostic approval remains pending.',
 'module_commit': 'c008b67e10fe91c3c5268926f44f59c521babba5', 'obs_revision': 5, 'srcmd5': '2f9526bbf3fc2b152ea2fce4bf451cf8',
 'targets': records,
 'core': 'Runtime/ONNX, SDK compiler, utilities and remote debugger checks pass on all three targets.',
 'diagnostics': {
  'approved': 'Python grpc_tools pkg_resources deprecation: evidence/grpc-tools-diagnostic-20261002.json.',
  'pending': "Connect AOT source fallback because optional module 'grpc' is now available. Six core phases each report it twice; no module suite fails.",
  'root_cause': 'Core is built before its optional grpc module. Loading Connect after installing grpc correctly selects source to expose ProtobufConnectCodec.',
  'paired_control': 'In an isolated Leap runtime container, Connect imports successfully from source with grpc installed, then from its AOT artifact after removing only qore-grpc-module. The exact warning appears only in the first invocation.',
  'proposal': 'Retain the exact diagnostic. No suppression, loader change, compiler flag or disabled functionality.'},
 'limits': ['Live Salesforce organization tests remain credential-dependent.', 'Current core source refresh, module branch CI integration, repository lifecycle and publication remain separate gates.'],
 'publication': 'disabled',
 'files_sha256': {str(p.relative_to(root)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}}
(root / 'evidence/grpc-native-installed-20261008.json').write_text(json.dumps(evidence, indent=2) + '\n')
print('PASS: 6 installed phases, 78 suite runs, 2274 cases, 10740 assertions; diagnostic decision pending')
