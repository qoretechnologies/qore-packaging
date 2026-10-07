# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import collections
import gzip
import hashlib
import json
import re
import shutil

root = Path.cwd()
output = root / 'evidence/controls/core-sdk22-canonical-final-20261007'
expected_commit = '49152d805b73c417db2bf3c0ac72dd22bfa8f058'
source = json.loads((root / 'work/qore-doc-sdk22-canonical-final-20261007/source-manifest.json').read_text())
assert source['commit'] == expected_commit and not source.get('candidate')
assert not source.get('packaging_overlay') and not source.get('source_overlay')
assert json.loads((root / 'results/core-sdk22-canonical-final-status-20261007.json').read_text()) == dict.fromkeys(('fedora', 'leap', 'el10'), 0)
assert json.loads((root / 'results/core-sdk22-canonical-installed-matrix-20261007.json').read_text()) == dict.fromkeys(('fedora', 'leap', 'el10'), 0)
output.mkdir(exist_ok=True)
targets = {}
for target in ('fedora', 'leap', 'el10'):
    base = root / f'results/{target}-core-sdk22-canonical-final-20261007'
    build = json.loads((base / 'build.json').read_text())
    assert build['exit_code'] == 0 and build['source'] == source
    data = (base / 'build.log').read_bytes()
    text = data.decode()
    assert text.count('Passed 400 out of 400 tests. 0 tests failed.') == 1
    assert not re.search(r'cpio:.*scanner\.lpp', text)
    for relative, expected in build['artifacts'].items():
        with (base / relative).open('rb') as stream:
            assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected, (target, relative)
    path = root / f'results/{target}-core-sdk22-canonical-final-installed-20261007.json'
    installed = json.loads(path.read_text())
    assert installed['exit_code'] == 0 and installed['source'] == source
    assert installed['artifacts'] == build['artifacts']
    assert set(installed['steps']) == {'sdk-install', 'sdk-tests', 'runtime-install', 'runtime-tests'}
    assert all(row['exit_code'] == 0 for row in installed['steps'].values())
    for name, step in installed['steps'].items():
        step_data = (root / step['log']).read_bytes()
        if name.endswith('-tests'):
            assert not re.search(rb'(?im)^warning:|^error:|^fatal:|CMake Warning|Unknown debugging section', step_data)
        (output / (target + '-' + name + '.log.gz')).write_bytes(gzip.compress(step_data, mtime=0))
    compiler = collections.Counter()
    for line in text.splitlines():
        if re.search(r'warning:.*\[-W', line):
            compiler[re.sub(r'/work/rpmbuild/BUILD/(?:qore-[^/]+-build/)?qore-[^/]+/', '', line)] += 1
    shutil.copy2(path, output / (target + '-installed.json'))
    shutil.copy2(base / 'build.json', output / (target + '-build.json'))
    (output / (target + '-build.log.gz')).write_bytes(gzip.compress(data, mtime=0))
    targets[target] = {'build_exit_code': 0, 'functional_suites': 400,
                       'installed': installed, 'compiler_diagnostics_pending_review': dict(compiler),
                       'debug_names_diagnostic_occurrences': text.count('Unknown debugging section .debug_names'),
                       'optional_aot_module_diagnostic_occurrences': text.count('qcc: warning: optional module')}
for name in ('build-core-sdk22-canonical-final-20261007.py',
             'after-core-sdk22-canonical-final-20261007.py',
             'qualify-core-sdk22-canonical-final-20261007.py'):
    shutil.copy2(root / 'work' / name, output / name)
shutil.copy2(__file__, output / 'record.py')
record = {
    'schema': 1, 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.', 'date': '2026-10-07',
    'status': 'Canonical core22 builds and installed runtime/SDK upgrades pass on all three x86_64 distributions. Unresolved build diagnostics, native OBS qualification and repository lifecycle still prevent publication.',
    'source_commit': expected_commit, 'source_manifest': source, 'targets': targets,
    'verified': ['All 1200 RPM functional suite runs pass; every retained artifact hash matches its build record.',
                 'Six installed phases upgrade the preserved core21 images, verify RPM payloads, and pass runtime/ONNX inference and session-pool checks.',
                 'SDK checks cover pkg-config, CMake embedding, qcc executables/modules, module-documentation capability, utilities and debugger launchers.',
                 'Minimal runtime inventories contain no Qore development package or C/C++ compiler.',
                 'The scanner debug-source copy error is absent after the verified Flex source-path fix.'],
    'limits': ['Compiler, optional-module build and debugedit diagnostics remain visible and are not approved by this result.',
               'Debugger launcher checks are not a claim of full debug-source integrity for every core AOT module.',
               'Fresh installation, whole-repository dependency resolution, module integration, removal and native ARM/OBS gates remain required.'],
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())},
}
(root / 'evidence/core-sdk22-canonical-final-20261007.json').write_text(json.dumps(record, indent=2) + '\n')
print('Canonical core22: 1200 functional suite runs and six installed phases pass; build diagnostics remain an open gate')
