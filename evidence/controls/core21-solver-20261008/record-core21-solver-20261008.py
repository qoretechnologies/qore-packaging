# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Verify and preserve package-name solver transactions and signed metadata controls."""
from pathlib import Path
import gzip
import hashlib
import json
import re
import runpy
import shutil
import subprocess

root = Path(__file__).resolve().parent.parent
out = root / 'evidence/controls/core21-solver-20261008'
out.mkdir(exist_ok=True)
prep = root / 'results/core21-solver-repositories-20261008'
prepared = json.loads((prep / 'status.json').read_text())
assert len(prepared['targets']) == 6 and prepared['private_key_retained'] is False
assert sum(v['packages'] for v in prepared['targets'].values()) == 86


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = source.read_bytes()
    assert not re.search(br'(?m)^-----BEGIN PGP PRIVATE KEY BLOCK-----$', data)
    assert source.suffix not in ('.rpm', '.gpg', '.keyring')
    if source.suffix in ('.log', '.txt'):
        destination.with_suffix(destination.suffix + '.gz').write_bytes(gzip.compress(data, mtime=0))
    else:
        destination.write_bytes(data)


for name, record in prepared['targets'].items():
    repository = root / record['repository']
    assert digest(root / record['manifest']) == record['manifest_sha256']
    for relative, expected in record['metadata_files'].items():
        assert digest(repository / relative) == expected, (name, relative)
        archive(repository / relative, out / 'repositories' / name / relative)
    assert digest(repository / 'metadata-public-key.asc') == prepared['metadata_public_key_sha256']
    assert 'BAD signature' in (prep / name / 'tampered-verification.log').read_text()
    assert 'Good signature' in (prep / name / 'verify.log').read_text()
    archive(repository / 'package-public-key.asc', out / 'repositories' / name / 'package-public-key.asc')
    archive(root / record['manifest'], out / 'repositories' / name / 'manifest.json')
for path in sorted(prep.rglob('*')):
    if path.is_file():
        archive(path, out / 'preparation' / path.relative_to(prep))

targets = {}
for name, directory in [('fedora', 'core21-solver-20261008'), ('el10', 'core21-solver-20261008'),
                        ('leap', 'core21-solver-leap-vendor-20261008')]:
    source = root / 'results' / directory / name
    record = json.loads((source / 'qualification.json').read_text())
    driver = json.loads((source / 'driver.json').read_text())
    assert record['exit_code'] == driver['exit_code'] == 0
    assert record['manifest'] == json.loads((root / f'results/core21-upgrade-baseline-20261008/{name}-x86_64/manifest.json').read_text())
    steps = {s['name']: s for s in record['steps']}
    assert len(steps) == len(record['steps'])
    required = {'reject-tampered-metadata', 'signed-repository-refresh', 'runtime-install-by-name',
                'sdk-install-by-name', 'runtime-rpm-verify', 'sdk-rpm-verify', 'runtime-runtime',
                'sdk-runtime', 'sdk-development', 'sdk-tools', 'sdk-remote-debuggers'}
    assert required <= steps.keys()
    for step in record['steps']:
        log = (source / (step['name'] + '.log')).read_text()
        if step['negative_control']:
            assert step['name'] == 'reject-tampered-metadata' and step['exit_code'] != 0
            assert re.search(r'(?i)(bad.*signature|signature.*(fail|invalid)|gpg.*(error|fail))', log)
        else:
            assert step['exit_code'] == 0
            assert not re.search(r'(?im)(\bwarning:|CMake Warning|CMake Error|^error:)', log), (name, step['name'])
    runtime = steps['runtime-install-by-name']['command']
    assert runtime[-1] == 'qore' and not any(a.endswith('.rpm') for a in runtime)
    if name == 'leap':
        assert '--allow-vendor-change' in runtime and '--no-recommends' in runtime
        text = (source / 'runtime-install-by-name.log').read_text()
        assert '1 package to upgrade, 51 new, 1 to change vendor.' in text
        assert 'libnghttp2-14\n  SUSE LLC' in text
    else:
        assert '--setopt=gpgcheck=True' in runtime and '--setopt=install_weak_deps=False' in runtime
    for phase in ('runtime', 'sdk'):
        assert not (source / (phase + '-rpm-verify.log')).read_text()
    inventory = (source / 'runtime-inventory.log').read_text()
    assert not re.search(r'(?m)^(qore-devel|gcc|gcc-c\+\+) ', inventory)
    for path in sorted(source.iterdir()):
        if path.is_file():
            archive(path, out / name / path.name)
    targets[name] = {'image': driver['image'], 'steps': len(record['steps']), 'architecture': 'x86_64',
                     'runtime_command': runtime, 'sdk_command': steps['sdk-install-by-name']['command'],
                     'tampered_metadata_rejected': True, 'runtime_without_compiler': True,
                     'runtime_and_sdk_rpm_verify': 'pass', 'onnx_inference_and_session_pool': 'pass',
                     'cpp_cmake_aot_tools_and_remote_debuggers': 'pass'}

initial = root / 'results/core21-solver-20261008/leap'
assert json.loads((initial / 'qualification.json').read_text())['exit_code'] != 0
assert 'requires \'libnghttp2-14(x86-64) >= 1.70.0\'' in (initial / 'runtime-install-by-name.log').read_text()
for name in ('runtime-install-by-name.log', 'qualification.json', 'driver.json'):
    archive(initial / name, out / 'leap-vendor-selection' / name)
archive(root / 'results/zypper-install-help-20261008.txt', out / 'leap-vendor-selection/zypper-install-help.txt')
for name in ('prepare-core21-solver-repositories-20261008.py', 'check-core21-solver-initial-20261008.py',
             'run-core21-solver-initial-20261008.py', 'check-core21-solver-20261008.py',
             'run-core21-solver-20261008.py', 'record-core21-solver-20261008.py'):
    archive(root / 'work' / name, out / name)
for name in ('tools/qualify-installed.py', 'tools/installed_jni.py', 'qualification/jni-fixtures.json'):
    archive(root / name, out / 'helper-snapshot' / name)
helper_tests = root / 'results/core21-solver-helper-tests-20261008.log'
text = helper_tests.read_text()
assert re.search(r'Ran 56 tests in [0-9.]+s\n\nOK\s*$', text)
assert not re.search(r'(?im)(warning:|^error:)', text)
archive(helper_tests, out / helper_tests.name)

write = runpy.run_path(str(root / 'work/write-scoped-audit.py'))['write']
passes = {
    9: 'New fixtures, documentation and evidence carry Copyright 2026; raw distribution outputs are preserved.',
    53: 'Use normal dependency resolution with signed metadata and signed packages. Leap explicitly selects a permitted vendor change for the requested transaction; no global vendor policy, signature bypass or dependency override.',
    54: 'Failed commands record nonzero status; private signing-key storage is temporary and package managers run only in disposable containers. Initial rejected Leap transaction remains archived.',
    55: 'Each parallel target has an independent container and output directory; metadata preparation is sequential.',
    56: 'Validated source manifests, unique package identities, checksums, key bytes and exact selected core versions are checked.',
    57: 'Repositories hardlink 86 cached RPMs. No duplicate payload archive or build image snapshot is created.',
    58: 'Six direct signature-tamper controls and three actual package-manager tamper controls reject altered metadata; valid metadata then refreshes and installs by package name.',
    59: 'The installation guide names tested commands, Leap vendor selection, EPEL/CRB prerequisites, ONNX coverage, publication status and ARM/cross-version exclusions.',
    61: 'RPMs retain original OBS signatures; ephemeral metadata public keys are hash-pinned. No private key, RPM binary or credential is archived. Installed tests run unprivileged.',
    62: 'All three x86_64 runtime/SDK solver transactions and 56 helper unit tests pass. Runtime excludes compiler packages, ONNX inference/session pool pass, SDK consumers/tools/debuggers pass and rpm -V is clean. Qualification steps emit no warnings.'}
write(out / 'audit.rst', 'Signed repository solver qualification audit',
      'Scope: local signed repository fixtures, completed package-manager transactions, installation documentation and evidence. '
      f'All 62 checks reviewed: {len(passes)} Pass, {62-len(passes)} N/A. No Qore/module implementation changes. '
      'Host/container bootstrap observations are recorded separately from the Qore qualification steps; no new diagnostic exception is inferred.',
      passes, 'No corresponding C++/Qore/QPP implementation, new module, DataProvider registration or JNI dependency change in this fixture/documentation scope.')

record = {'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
          'status': 'All three clean x86_64 signed local repository solver installs and installed runtime/SDK suites pass.',
          'source_commit': 'd58eec0b2ab721ef5da0e2136c4cddb3579874e2',
          'obs_core_srcmd5': 'ba3b6bc9ac8055ee991e334102e7ad16',
          'metadata_preparation': {'targets': 6, 'signed_rpms': 86, 'negative_controls': 6,
                                   'private_key_retained': False,
                                   'ephemeral_fingerprint': prepared['temporary_metadata_key_fingerprint']},
          'targets': targets,
          'leap_vendor_selection': 'The first by-name install rejected the newer project libnghttp2 because the installed SUSE vendor is sticky. The final transaction explicitly allows vendor change and upgrades only libnghttp2-14; no persistent solver-policy change.',
          'bootstrap_observations': ['Before Qore qualification, AlmaLinux util-linux installation preserves an existing unowned /etc/adjtime and writes /etc/adjtime.rpmnew. The base image contains 0.0 0 0.0, 0, UTC. The raw bootstrap log is retained separately; no warning suppression or diagnostic exception is inferred.'],
          'limits': ['Metadata is signed by an ephemeral local fixture key, not the production OBS repository key; this is not a production publication check.',
                     'Native aarch64 metadata sets pass direct checks, but package-manager solver installation is x86_64 only.',
                     'Cross-version upgrades, module co-installation and final public repository metadata remain separate gates.',
                     'The archived test signing key expires after one day; reproductions must generate a fresh fixture key.'],
          'documentation': 'docs/repository-installation.rst',
          'documentation_sha256': {name: digest(root / name) for name in
                                    ('docs/repository-installation.rst', 'docs/source-and-build-workflow.rst')},
          'files_sha256': {str(p.relative_to(root)): digest(p) for p in sorted(out.rglob('*')) if p.is_file()}}
(root / 'evidence/core21-solver-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS: six metadata sets, 86 signed RPMs, six direct and three package-manager tamper rejections, three successful solver/runtime/SDK sequences')
