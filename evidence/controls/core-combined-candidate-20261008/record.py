# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Retain completed candidate evidence without approving unresolved diagnostics."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil

root = Path('/home/david/src/qore/git/qore-packaging')
output = root / 'evidence/controls/core-combined-candidate-20261008'
output.mkdir()
source = json.loads((root / 'work/core-fixes-combined-candidate-20261008/source-manifest.json').read_text())
assert source['candidate'] is True and len(source['source_overlay']) == 65
assert json.loads((root / 'results/core-fixes-combined-candidate-20261008-status.json').read_text())['exit_code'] == 0
assert json.loads((root / 'results/core-combined-installed-followup-20261008.json').read_text())['exit_code'] == 0
targets = {}
for target in ('fedora', 'leap', 'el10'):
    directory = output / target
    directory.mkdir()
    base = root / f'results/{target}-core-fixes-combined-candidate-20261008'
    build = json.loads((base / 'build.json').read_text())
    assert build['exit_code'] == 0 and build['source'] == source
    assert len(build['artifacts']) == 15
    for relative, digest in build['artifacts'].items():
        with (base / relative).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == digest, (target, relative)
    raw = (base / 'build.log').read_bytes()
    log = raw.decode()
    assert log.count('Passed 405 out of 405 tests. 0 tests failed.') == 1
    ml = log.split('+ build/qore -b --enable-debug modules/ml/test/ml.qtest -v\n', 1)[1].split('\n+ ', 1)[0]
    assert 'Ran 346 test cases, 346 succeeded (3027 assertions)' in ml
    assert len(re.findall(r'^Skipped:', ml, re.M)) == 11
    assert len(re.findall(r'^Success:', ml, re.M)) == 335
    installed_path = root / f'results/{target}-core-combined-candidate-installed-20261008.json'
    installed = json.loads(installed_path.read_text())
    assert installed['exit_code'] == 0
    assert installed['source'] == source and installed['artifacts'] == build['artifacts']
    assert set(installed['steps']) == {'sdk-install', 'sdk-tests', 'runtime-install', 'runtime-tests'}
    for name, step in installed['steps'].items():
        assert step['exit_code'] == 0
        data = (root / step['log']).read_bytes()
        if name.endswith('-tests'):
            assert not re.search(rb'(?im)^warning:|^error:|^fatal:|CMake Warning|Unknown debugging section', data)
        (directory / (name + '.log.gz')).write_bytes(gzip.compress(data, mtime=0))
    compiler = Counter(re.sub(r'/work/rpmbuild/BUILD/(?:qore-[^/]+-build/)?qore-[^/]+/', '', line)
                       for line in log.splitlines() if re.search(r'warning:.*\[-W', line))
    diagnostics = {'compiler': dict(compiler),
                   'optional_module_occurrences': log.count('qcc: warning: optional module'),
                   'debug_names_occurrences': log.count('Unknown debugging section .debug_names'),
                   'status': 'Retained for review; this record grants no diagnostic exception.'}
    (directory / 'diagnostics.json').write_text(json.dumps(diagnostics, indent=2) + '\n')
    (directory / 'build.log.gz').write_bytes(gzip.compress(raw, mtime=0))
    shutil.copy2(base / 'build.json', directory / 'build.json')
    shutil.copy2(installed_path, directory / 'installed.json')
    targets[target] = {'build_exit_code': 0, 'rpms': 15, 'functional_suites': 405,
                       'ml_reported_cases': 346, 'ml_executed_cases': 335,
                       'ml_accelerator_skips': 11, 'ml_assertions': 3027,
                       'runtime_upgrade_exit_code': 0, 'sdk_upgrade_exit_code': 0,
                       'runtime_image': installed['runtime_image'], 'sdk_image': installed['sdk_image'],
                       'compiler_diagnostic_occurrences_pending_review': sum(compiler.values()),
                       'compiler_diagnostic_sites_pending_review': len(compiler)}
for name in ('qualify-core-combined-candidate-20261008.py', 'after-core-combined-candidate-20261008.py'):
    shutil.copy2(root / 'work' / name, output / name)
shutil.copy2(__file__, output / 'record.py')
record = {
    'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'Combined candidate RPM builds and core21-to-candidate installed runtime/SDK upgrades pass on all three x86_64 distributions. Source commitment, diagnostics, native builds and repository publication remain open gates.',
    'source_manifest': source, 'targets': targets,
    'verified': ['All 45 RPM hashes match their completed build manifests.',
                 'All 1215 core functional suite runs pass.',
                 'The three ML runs execute 1005 cases with 9081 reported assertions; 33 accelerator-only cases are explicitly skipped because these packages provide CPU ONNX Runtime.',
                 'All six installed upgrade phases pass rpm -V and runtime tests without warning/error output, including CPU ONNX inference and session pooling.',
                 'All three SDK phases additionally pass pkg-config/CMake embedding, AOT executables and source-free modules, metadata/documentation helpers, utilities and debugger launchers.',
                 'The runtime images contain no Qore development package or C/C++ compiler.'],
    'limits': ['The source contains a qualification-only overlay and cannot be uploaded to OBS or published. A reviewed committed canonical build is required.',
               'Core compiler, optional-module and debug-artifact diagnostics remain visible and unresolved; no new exception or suppression is introduced.',
               'Local candidate RPMs are unsigned. Clean signed native OBS installation, final module integration, repository lifecycle and publication gates remain required.',
               'Successful debugger launcher checks do not resolve the separate full AOT debug-information proposal.'],
    'files_sha256': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted(output.rglob('*')) if path.is_file()},
}
(root / 'evidence/core-combined-candidate-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('Verified: 45 RPMs, 1215 core suites, 1005 executed ML cases and six installed upgrade phases')
