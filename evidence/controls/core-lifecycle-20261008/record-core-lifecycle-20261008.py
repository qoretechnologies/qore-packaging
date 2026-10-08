# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import runpy
import shutil

root = Path(__file__).resolve().parent.parent
out = root / 'evidence/controls/core-lifecycle-20261008'
out.mkdir(exist_ok=True)

def archive(source, destination):
    data = source.read_bytes()
    assert source.suffix not in ('.rpm', '.gpg')
    assert not re.search(br'(?m)^-----BEGIN (?:PGP )?PRIVATE KEY', data)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix == '.log':
        destination.with_suffix('.log.gz').write_bytes(gzip.compress(data, mtime=0))
    else:
        destination.write_bytes(data)

results = {}
for target in ('fedora', 'leap', 'el10'):
    folder = 'core-lifecycle-leap-https-20261008' if target == 'leap' else 'core-lifecycle-local-20261008'
    source = root / 'results' / folder
    pins = json.loads((source / 'source.json').read_text())
    assert all(hashlib.sha256((root / n).read_bytes()).hexdigest() == h for n, h in pins.items())
    driver = json.loads((source / target / 'driver.json').read_text())
    assert driver['exit_code'] == 0
    directory = source / target / 'qualification'
    record = json.loads((directory / 'qualification.json').read_text())
    assert record['exit_code'] == 0 and record['machine'] == 'x86_64'
    assert record['repository']['private_key_retained'] is False
    lifecycle = record['core_lifecycle']
    assert lifecycle['exact_inventory_restored'] and lifecycle['unrelated_packages_preserved']
    assert lifecycle['payload_files_checked'] == (12423 if target == 'leap' else 12833)
    steps = {s['name']: s for s in record['steps']}
    assert len(steps) == len(record['steps'])
    for step in record['steps']:
        text = (directory / (step['name'] + '.log')).read_text()
        if step.get('expected_signature_rejection'):
            assert step['name'] == 'repository-reject-tampered' and step['exit_code'] != 0
        elif step.get('expected_dependency_rejection'):
            assert step['name'] == 'lifecycle-reject-library-removal' and step['exit_code'] == 1
        else:
            assert step['exit_code'] == 0
            assert not re.search(r'(?im)(\bwarning:|CMake (?:Warning|Error)|^error:)', text), (target, step['name'])
    for suite in ('runtime', 'development', 'tools', 'remote-debuggers'):
        assert steps['reinstalled-' + suite]['command'][:4] == ['runuser', '-u', 'qoretester', '--']
    for phase in ('runtime', 'sdk', 'lifecycle'):
        assert not (directory / (phase + '-rpm-verify.log')).read_bytes()
    for name in lifecycle['core_packages']:
        assert (directory / ('lifecycle-repository-header-' + name + '.log')).read_bytes() == (
            directory / ('lifecycle-repository-selected-' + name + '.log')).read_bytes()
    assert sorted((directory / 'lifecycle-before.log').read_text().splitlines()) == sorted(
        (directory / 'lifecycle-restored-inventory.log').read_text().splitlines())
    results[target] = {'steps': len(steps), 'image': driver['image'], 'exit_code': 0,
                       'lifecycle': lifecycle, 'runtime_sdk_onnx_tools_debuggers_after_reinstall': 'pass',
                       'repository': record['repository']}
    archive(source / 'source.json', out / target / 'source.json')
    for path in sorted((source / target).rglob('*')):
        if path.is_file():
            archive(path, out / target / path.relative_to(source / target))

initial = root / 'results/core-lifecycle-local-20261008/leap'
assert json.loads((initial / 'driver.json').read_text())['exit_code'] == 104
for path in initial.glob('driver.*'):
    archive(path, out / 'leap-initial-http-bootstrap' / path.name)
for name in ('leap-bootstrap-network-20261008.json', 'leap-bootstrap-repo-config-20261008.log',
             'core-lifecycle-all-unit-final-20261008.log'):
    archive(root / 'results' / name, out / name)
tests = (root / 'results/core-lifecycle-all-unit-final-20261008.log').read_text()
assert 'Ran 245 tests' in tests and tests.rstrip().endswith('OK') and 'Warning' not in tests
for name, expected in [('ordinary', {'packaging-tools'}),
                       ('all', {'packaging-tools', 'rpm-lifecycle-fedora-arm64', 'rpm-lifecycle-leap-arm64', 'rpm-lifecycle-el10-arm64'}),
                       ('fedora', {'packaging-tools', 'rpm-lifecycle-fedora-arm64'})]:
    path = root / 'results' / ('core-lifecycle-ci-' + name + '-final-20261008.json')
    lint = json.loads(path.read_text())
    assert lint['valid'] and not lint['errors'] and not lint['warnings']
    assert {j['name'] for j in lint['jobs']} == expected
    archive(path, out / path.name)
for name in ('qualify-core-lifecycle-local-20261008.py', 'qualify-core-lifecycle-leap-https-20261008.py',
             'record-core-lifecycle-20261008.py'):
    archive(root / 'work' / name, out / name)

passes = {
    9: 'New helper, tests and evidence carry Copyright 2026; existing runner and CI retain it.',
    53: 'Uses ordinary package-manager removal and signed repository reinstall by name. Retaining dependencies is an explicit transaction option. Leap uses HTTPS on the same official CDN, fixing the failing HTTP bootstrap transport without changing sources, packages or verification.',
    54: 'Repository ExitStack cleanup remains in force on every failure. Tests inject removal, reinstall, inventory, version and verification failures; runner tests verify cleanup after lifecycle and post-install failures.',
    55: 'All lifecycle state belongs to one invocation. Each native fixture uses a separate container and repository alias.',
    56: 'Existing manifest validation runs before lifecycle scope checks. Exactly seven named core packages are accepted; module manifests, duplicates, wrong sources and additional core payloads are rejected.',
    57: 'Reuses downloaded signed RPMs, generated repository and existing unprivileged suites. Inventory and payload checks are linear plus sorting; no additional full build is introduced.',
    58: 'Tests cover malformed/empty inventories and payloads, traversal, dangling symlinks, surviving executables, dependency rejection misclassification, changed unrelated packages and all three distribution transaction paths.',
    59: 'Workflow documents the opt-in CLI and ARM jobs, requirements, exact preservation checks, repeated ONNX/SDK tests, cleanup and distinction from cross-version upgrades.',
    61: 'Only an exact seven-package set can be removed in the fixture; all unrelated packages must be unchanged. Package/metadata signatures remain required and tests run unprivileged. No private signing key is retained.',
    62: 'All 245 unit tests and three actual native x86_64 sequences pass. Each removes every core payload file, restores exact inventory and repeats four runtime/SDK/tool suites without unexpected diagnostics. GitLab validates ordinary, all-ARM and Fedora-only job selection.'}
audit = root / 'audits/core-lifecycle-20261008.rst'
runpy.run_path(str(root / 'work/write-scoped-audit.py'))['write'](audit, 'Core repository lifecycle runner audit',
    'Scope: core_lifecycle.py, qualify-installed.py integration, regression tests, three explicit native ARM jobs and workflow documentation. '
    'All 62 checks reviewed: 10 Pass, 52 N/A, 0 Fail. Three native x86_64 runs complete; native ARM execution is the next gate.',
    passes, 'No C++/Qore/QPP implementation, installed module, DataProvider, JNI dependency or cancellation-point change in this Python/CI fixture scope.')
paths = ['tools/core_lifecycle.py', 'tools/qualify-installed.py', 'tests/test_core_lifecycle.py',
         '.gitlab-ci.yml', 'docs/source-and-build-workflow.rst', str(audit.relative_to(root))]
record = {'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
          'status': 'Qualified on all three native x86_64 distributions; native ARM execution pending.',
          'targets': results, 'tool_tests': 245, 'audit': {'pass': 10, 'na': 52, 'fail': 0, 'path': str(audit.relative_to(root))},
          'bootstrap': 'Initial Leap HTTP CDN bootstrap returned 503 before any Qore qualification. The same official HTTPS endpoint returned 200; repository configs and their owning service index now use HTTPS. Signature enforcement is unchanged.',
          'limits': ['Same-version removal/reinstall only; cross-version upgrades and full module co-installation remain separate gates.',
                     'Ephemeral fixture metadata signing does not qualify production OBS repository publication.',
                     'Native ARM execution remains required; no pending diagnostic decision is implicitly accepted.'],
          'source_sha256': {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths},
          'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}}
(root / 'evidence/core-lifecycle-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS: 245 tests, three native lifecycle sequences, three CI selection controls, all 62 audit entries')
