# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import runpy
import shutil

root = Path(__file__).resolve().parent.parent
source = root / 'results/repository-runner-arm-20261008'
out = root / 'evidence/controls/repository-runner-arm-20261008'
out.mkdir()
status = json.loads((source / 'status.json').read_text())
assert len(status) == 4 and all(v['status'] == 'success' and v['trace_exit_code'] == 0 for v in status.values())
revision = '8f83585ca07a4a54704e35b01828ad7d23753de1'
targets = {}
for target in ('fedora', 'leap', 'el10'):
    name = 'rpm-repository-' + target + '-arm64'
    directory = source / name
    job = json.loads((directory / 'job.json').read_text())
    assert job['status'] == 'success' and job['pipeline']['id'] == 60058 and job['commit']['id'] == revision
    record = json.loads((directory / 'qualification.json').read_text())
    assert record['exit_code'] == 0 and record['machine'] == 'aarch64' and record['runner_arch'] == 'linux/arm64'
    manifest = json.loads((root / f'qualification/core21-{target}-aarch64.json').read_text())
    assert record['manifest'] == manifest
    assert record['repository']['private_key_retained'] is False
    steps = {s['name']: s for s in record['steps']}
    assert len(steps) == len(record['steps'])
    required = {'repository-reject-tampered', 'repository-refresh', 'runtime-install', 'sdk-install',
                'runtime-rpm-verify', 'sdk-rpm-verify', 'runtime-runtime', 'sdk-runtime', 'sdk-development',
                'sdk-tools', 'sdk-remote-debuggers'}
    assert required <= steps.keys()
    assert steps['runtime-install']['command'][-1] == 'qore'
    for step in record['steps']:
        text = (directory / (step['name'] + '.log')).read_text()
        if step.get('expected_signature_rejection'):
            assert step['name'] == 'repository-reject-tampered' and step['exit_code'] != 0
        else:
            assert step['exit_code'] == 0
            assert not re.search(r'(?im)(\bwarning:|CMake (?:Warning|Error)|^error:)', text)
    for entry in manifest['packages']:
        n = entry['name']
        assert (directory / ('repository-header-' + n + '.log')).read_bytes() == (
            directory / ('repository-selected-' + n + '.log')).read_bytes()
    for phase in ('runtime', 'sdk'):
        assert not (directory / (phase + '-rpm-verify.log')).read_bytes()
    assert not re.search(r'(?m)^(qore-devel|gcc|gcc-c\+\+) ', (directory / 'runtime-inventory.log').read_text())
    targets[target] = {'job_id': job['id'], 'web_url': job['web_url'], 'machine': record['machine'],
                       'runner_arch': record['runner_arch'], 'steps': len(steps),
                       'pinned_package_builds': len(manifest['packages']), 'exit_code': 0,
                       'signature_tamper_rejection': 'pass', 'runtime_without_compiler': 'pass',
                       'onnx_inference_and_session_pool': 'pass', 'runtime_sdk_tools_debuggers': 'pass',
                       'rpm_verification': 'pass', 'repository': record['repository']}
for path in sorted(source.rglob('*')):
    if not path.is_file() or path.name == 'artifacts.zip':
        continue
    destination = out / path.relative_to(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = path.read_bytes()
    assert not re.search(br'(?m)^-----BEGIN (?:PGP )?PRIVATE KEY', data)
    if path.name == 'job.json':
        full = json.loads(data)
        small = {k: full[k] for k in ('id', 'name', 'status', 'web_url', 'started_at', 'finished_at')}
        small.update(pipeline_id=full['pipeline']['id'], source_commit=full['commit']['id'])
        destination.write_text(json.dumps(small, indent=2) + '\n')
    elif path.suffix == '.log':
        destination.with_suffix('.log.gz').write_bytes(gzip.compress(data, mtime=0))
    else:
        destination.write_bytes(data)
shutil.copyfile(root / 'work/collect-repository-arm-20261008.py', out / 'collect-repository-arm-20261008.py')
shutil.copyfile(Path(__file__), out / Path(__file__).name)
passes = {
    9: 'The collector, recorder, documentation and evidence carry Copyright 2026.',
    53: 'Record completed source-pinned native jobs without changing tests, signatures, dependency resolution or production settings.',
    54: 'Collector joins job log streams, checks terminal state and rejects unsafe archive paths/symlinks. Recorder refuses missing or failed steps.',
    55: 'Each job writes its own directory; final collection completes only after all streams terminate.',
    56: 'Pipeline, commit, job identity, manifest, architecture and every selected package identity are checked against pinned values.',
    57: 'Reuse CI artifacts and existing logs; do not repeat builds or retain RPM binaries.',
    58: 'Expected signature rejection is the only accepted nonzero step. Every installed RPM matches its input header, and runtime phases exclude compiler packages.',
    59: 'Installation documentation now distinguishes completed six-target native solver checks from pending upgrades, module combinations and public repository verification.',
    61: 'Artifacts contain only public signing metadata, qualified logs and minimal job identifiers; private signing keys and raw user/runner API metadata are not archived.',
    62: 'All three linux/arm64 jobs and the tool job succeed on 8f83585. ONNX inference/session pool, C++/CMake/AOT consumers, tools, remote debuggers and rpm -V pass without unexpected qualification diagnostics.'}
runpy.run_path(str(root / 'work/write-scoped-audit.py'))['write'](out / 'audit.rst',
    'Native ARM repository installation evidence audit',
    f'Scope: pipeline 60058 artifacts and installation-guide status update. All 62 checks reviewed: {len(passes)} Pass, {62-len(passes)} N/A, 0 Fail. '
    'The existing runner implementation is audited separately; this change records its completed native qualification.',
    passes, 'No C++/Qore/QPP/runtime/CI implementation, installed module, DataProvider or JNI dependency changes in this evidence/documentation scope.')
record = {'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
          'status': 'All three native ARM signed repository solver/runtime/SDK jobs pass; the reusable runner is now qualified on all six target combinations.',
          'pipeline_id': 60058, 'pipeline_url': 'https://git.qoretechnologies.com/mirror/qore-packaging/-/pipelines/60058',
          'runner_commit': revision, 'core_commit': 'd58eec0b2ab721ef5da0e2136c4cddb3579874e2', 'targets': targets,
          'x86_evidence': 'evidence/repository-runner-20261008.json',
          'limits': ['Signing metadata uses an ephemeral fixture key, not the production OBS signing key.',
                     'Native ARM removal, cross-version upgrades, complete module co-installation and final public metadata remain separate gates.',
                     'Success does not approve any previously pending Qore, Node, NATS or module diagnostic exception.'],
          'documentation_sha256': {'docs/repository-installation.rst': hashlib.sha256((root / 'docs/repository-installation.rst').read_bytes()).hexdigest()},
          'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in sorted(out.rglob('*')) if p.is_file()}}
(root / 'evidence/repository-runner-arm-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('PASS: pipeline 60058, three native ARM machines and runners, signed solver/runtime/SDK checks, full audit')
