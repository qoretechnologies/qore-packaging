# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import runpy
import shutil

root = Path(__file__).resolve().parent.parent
out = root / 'evidence/controls/repository-runner-20261008'
out.mkdir()
source = root / 'results/repository-runner-local-20261008'
status = json.loads((source / 'status.json').read_text())
assert set(status) == {'fedora', 'leap', 'el10'} and all(v['exit_code'] == 0 for v in status.values())
pins = json.loads((source / 'source.json').read_text())
for name, digest in pins.items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, name
results = {}
for target in ('fedora', 'leap', 'el10'):
    directory = source / target / 'qualification'
    record = json.loads((directory / 'qualification.json').read_text())
    assert record['exit_code'] == 0 and record['machine'] == 'x86_64'
    assert record['repository']['private_key_retained'] is False
    steps = {s['name']: s for s in record['steps']}
    for step in record['steps']:
        text = (directory / (step['name'] + '.log')).read_text()
        if step.get('expected_signature_rejection'):
            assert step['name'] == 'repository-reject-tampered' and step['exit_code'] != 0
        else:
            assert step['exit_code'] == 0
            assert not re.search(r'(?im)(\bwarning:|CMake (?:Warning|Error)|^error:)', text), (target, step['name'])
    assert steps['runtime-install']['command'][-1] == 'qore'
    assert steps['repository-reject-tampered']['expected_signature_rejection']
    assert {'runtime-runtime', 'sdk-runtime', 'sdk-development', 'sdk-tools', 'sdk-remote-debuggers'} <= steps.keys()
    for entry in record['manifest']['packages']:
        name = entry['name']
        assert (directory / ('repository-header-' + name + '.log')).read_bytes() == (
            directory / ('repository-selected-' + name + '.log')).read_bytes()
    for phase in ('runtime', 'sdk'):
        assert not (directory / (phase + '-rpm-verify.log')).read_bytes()
    results[target] = {'steps': len(steps), 'image': status[target]['image'], 'selected_package_builds': len(record['manifest']['packages']),
                       'signature_tamper_rejection': 'pass', 'runtime_sdk_and_onnx': 'pass',
                       'repository': record['repository']}
for path in sorted(source.rglob('*')):
    if not path.is_file():
        continue
    assert path.suffix not in ('.rpm', '.gpg')
    data = path.read_bytes()
    assert not re.search(br'(?m)^-----BEGIN PGP PRIVATE KEY BLOCK-----$', data)
    dest = out / path.relative_to(source)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == '.log':
        dest.with_suffix('.log.gz').write_bytes(gzip.compress(data, mtime=0))
    else:
        dest.write_bytes(data)
for name in ('repository-runner-all-tests-20261008.log', 'repository-fixture-unit-20261008.log'):
    data = (root / 'results' / name).read_bytes()
    assert data.rstrip().endswith(b'OK')
    (out / (name + '.gz')).write_bytes(gzip.compress(data, mtime=0))
assert 'Ran 238 tests' in (root / 'results/repository-runner-all-tests-20261008.log').read_text()
for name, expected in [('final', {'packaging-tools', 'rpm-repository-fedora-arm64', 'rpm-repository-leap-arm64', 'rpm-repository-el10-arm64'}),
                       ('ordinary', {'packaging-tools'}), ('fedora', {'packaging-tools', 'rpm-repository-fedora-arm64'})]:
    filename = ('repository-runner-ci-lint-final-20261008.json' if name == 'final' else
                'repository-runner-ci-' + name + '-20261008.json')
    path = root / 'results' / filename
    record = json.loads(path.read_text())
    assert record['valid'] and not record['errors'] and not record['warnings']
    assert {j['name'] for j in record['jobs']} == expected
    shutil.copyfile(path, out / filename)
for name in ('qualify-repository-runner-local-20261008.py', 'record-repository-runner-20261008.py'):
    shutil.copyfile(root / 'work' / name, out / name)
passes = {
    9: 'New helper, tests and evidence carry Copyright 2026; existing runner and CI retain it.',
    53: 'The opt-in mode uses normal repository discovery and dependency solving. No bypass of checksums, package signatures, metadata signatures or dependency requirements. Leap vendor selection is limited to the requested transaction.',
    54: 'TemporaryDirectory and ExitStack remove private keys and owned repository configs on success or failure. Tests inject failures during key generation, signing, negative control, refresh and consumer execution on each package-manager family.',
    55: 'All mutable fixture state is local to one invocation; each container has its own output and generated repository alias.',
    56: 'The existing manifest validator constrains package names, phases, architectures, immutable source revisions and hashes. Generated metadata must match that exact inventory and native architecture checks precede installation.',
    57: 'One metadata generation and signing pass per run. Existing runner downloads, unprivileged logging and installed suites are reused; normal explicit-RPM mode is unchanged.',
    58: 'Controls reject unsafe metadata paths, mismatched hashes/inventories, duplicate indexes/packages, false signature failures and changed epoch/version/release/architecture. Runtime requests qore and explicit modules so transitive dependencies are resolved by the package manager.',
    59: 'The guide documents CLI/CI invocation, matching-native-container requirement, fixture tool prerequisites, ephemeral key handling, retained evidence and separation from production publication.',
    61: 'Keys are generated in mode-0700 temporary storage and removed before installation. Only public keys/metadata/logs are retained. Configs are exclusively created and cleanup preserves unrelated files; all installed tests remain unprivileged.',
    62: 'All 238 tool tests and three fresh x86_64 actual repository/runtime/SDK sequences pass without qualification-step warnings. GitLab lint passes default, all-three and Fedora-only selection; ordinary pipelines contain no native qualification job.'}
audit_path = root / 'audits/repository-install-runner-20261008.rst'
runpy.run_path(str(root / 'work/write-scoped-audit.py'))['write'](audit_path, 'Native repository installation runner audit',
    'Scope: repository_fixture.py, the opt-in qualify-installed.py path, repository tests, three explicit ARM CI jobs and the workflow guide. '
    f'All 62 checks reviewed: {len(passes)} Pass, {62-len(passes)} N/A, 0 Fail. '
    'Actual qualification is currently x86_64; native ARM execution remains a required next step. '
    'The initial lint request required an explicit JSON content-type header; the corrected server checks pass without configuration changes.',
    passes, 'No corresponding C++/Qore/QPP implementation, installed module, DataProvider registration, JNI dependency or cancellation-point change in this Python/CI fixture scope.')
paths = ['.gitlab-ci.yml', 'docs/source-and-build-workflow.rst', 'tools/qualify-installed.py',
         'tools/repository_fixture.py', 'tests/test_repository_fixture.py', str(audit_path.relative_to(root))]
record = {'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
          'status': 'Reusable signed repository mode passes all tool tests and all three fresh x86_64 distribution checks; native ARM execution pending.',
          'targets': results, 'tool_tests': 238, 'ci_selection': {'ordinary': 'tools only', 'core21-solver': 'three ARM jobs', 'target-fedora': 'one ARM job'},
          'audit': {'pass': len(passes), 'na': 62-len(passes), 'fail': 0, 'path': str(audit_path.relative_to(root))},
          'limits': ['Ephemeral local metadata signing does not qualify production OBS repository publication.',
                     'Native ARM, cross-version upgrades and complete module co-installation remain separate gates.',
                     'Distribution bootstrap logs are retained; no new external diagnostic exception is inferred.'],
          'source_sha256': {p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths},
          'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(out.rglob('*')) if p.is_file()}}
(root / 'evidence/repository-runner-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS: 238 tool tests; three real signed repository/runtime/SDK sequences; three valid CI selection controls; full audit')
