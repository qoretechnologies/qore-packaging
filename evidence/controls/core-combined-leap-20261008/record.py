# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Record completed Leap candidate qualification without approving diagnostics."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

root = Path('/home/david/src/qore/git/qore-packaging')
base = root / 'results/leap-core-fixes-combined-candidate-20261008'
output = root / 'evidence/controls/core-combined-leap-20261008'
output.mkdir()
build = json.loads((base / 'build.json').read_text())
assert build['exit_code'] == 0 and len(build['artifacts']) == 15
source = json.loads((root / 'work/core-fixes-combined-candidate-20261008/source-manifest.json').read_text())
assert source == build['source'] and source['candidate'] is True
assert len(source['source_overlay']) == 65
for relative, expected in build['artifacts'].items():
    with (base / relative).open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected, relative
for relative, expected in source['sources'].items():
    with (root / 'work/core-fixes-combined-candidate-20261008' / relative).open('rb') as stream:
        assert hashlib.file_digest(stream, 'sha256').hexdigest() == expected, relative
raw = (base / 'build.log').read_bytes()
log = raw.decode()
assert log.count('Passed 405 out of 405 tests. 0 tests failed.') == 1
ml = log.split('+ build/qore -b --enable-debug modules/ml/test/ml.qtest -v\n', 1)[1].split('\n+ ', 1)[0]
assert 'Ran 346 test cases, 346 succeeded (3027 assertions)' in ml
assert len(re.findall(r'^Skipped:', ml, re.M)) == 11
assert len(re.findall(r'^Success:', ml, re.M)) == 335
compiler = Counter(re.sub(r'/work/rpmbuild/BUILD/(?:qore-[^/]+-build/)?qore-[^/]+/', '', line)
                   for line in log.splitlines() if re.search(r'warning:.*\[-W', line))
previous = json.loads((root / 'evidence/core-sdk22-canonical-final-20261007.json').read_text())
assert compiler == previous['targets']['leap']['compiler_diagnostics_pending_review']
installed_path = root / 'results/leap-core-combined-candidate-installed-20261008.json'
installed = json.loads(installed_path.read_text())
assert installed['exit_code'] == 0
assert installed['source'] == source and installed['artifacts'] == build['artifacts']
assert set(installed['steps']) == {'sdk-install', 'sdk-tests', 'runtime-install', 'runtime-tests'}
for name, step in installed['steps'].items():
    assert step['exit_code'] == 0, name
    data = (root / step['log']).read_bytes()
    if name.endswith('-tests'):
        assert not re.search(rb'(?im)^warning:|^error:|^fatal:|CMake Warning|Unknown debugging section', data)
    (output / (name + '.log.gz')).write_bytes(gzip.compress(data, mtime=0))
directories = json.loads((root / 'results/core-combined-leap-artifacts-20261008/application-directories.json').read_text())
assert directories['exit_code'] == 0 and directories['application_rpms'] == 9
assert not any(directories['results'].values())
shutil.copy2(base / 'build.json', output / 'build.json')
shutil.copy2(installed_path, output / 'installed.json')
(output / 'build.log.gz').write_bytes(gzip.compress(raw, mtime=0))
for name in ('application-directories.json', 'directories.json', 'stderr.log', 'command.json'):
    shutil.copy2(root / 'results/core-combined-leap-artifacts-20261008' / name, output / name)
shutil.copy2(root / 'work/qualify-core-combined-candidate-20261008.py', output / 'qualify-installed.py')
shutil.copy2(__file__, output / 'record.py')
qore = root.parent / 'qore'
head = subprocess.check_output(['git', '-C', str(qore), 'rev-parse', 'HEAD'], text=True).strip()
assert head == '9951c7d3e7d797a113e1c1274ce1aa7dcc34a376'
assert not subprocess.check_output(['git', '-C', str(qore), 'status', '--porcelain'])
record = {
    'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'Leap x86_64 candidate build and core21-to-candidate runtime/SDK upgrade tests pass. This is qualification evidence, not an upload or publication approval.',
    'source_manifest': source,
    'build': {'exit_code': 0, 'artifacts': build['artifacts'], 'core_suites': 405,
              'ml_reported_cases': 346, 'ml_executed_cases': 335, 'ml_expected_accelerator_skips': 11,
              'ml_assertions': 3027, 'onnx_required': True},
    'installed': installed,
    'verified': ['All 15 RPM hashes match their build manifest.',
                 'The runtime and SDK upgrade the retained core21 images and pass rpm -V.',
                 'Runtime tests pass CPU ONNX model inference and session pooling, native/source/AOT module imports, and all four execution modes.',
                 'SDK tests pass pkg-config and CMake embedding, qcc executables and source-free modules, documentation helpers, utilities and debugger launchers.',
                 'Both installed test phases have no warning/error output; the minimal runtime has no compiler or Qore development package.',
                 'All nine application RPMs pass the documented parent-directory ownership check.'],
    'directory_scope': directories,
    'diagnostics': {'compiler_pending_review': dict(compiler),
                    'comparison': 'Exact same eight compiler records as the previous Leap canonical core22 build; equality is not approval.',
                    'optional_aot_module_warning_occurrences': log.count('qcc: warning: optional module'),
                    'debug_names_warning_occurrences': log.count('Unknown debugging section .debug_names')},
    'develop_sync': {'previous': 'e897fe2524fcb95f6fe3c1de85b270e147aa655a', 'head': head,
                     'method': 'Clean fast-forward of the remote notifier-header fix; existing source fixes remain in develop.',
                     'candidate_unchanged': True},
    'limits': ['The candidate has a source overlay and cannot be uploaded or published. A committed canonical source build remains required.',
               'Compiler, optional-module, negative-test and AOT debugger diagnostic gates remain open; this evidence grants no new exception.',
               'The initial directory invocation included automatic debug RPMs outside the documented application scope. Its one /usr/src/debug result is retained; the separate debug-artifact gate remains open.',
               'Local candidate RPMs are unsigned. Signed native OBS installation and full repository integration remain required.',
               'Fedora and AlmaLinux builds are still active; their installed tests are queued behind process completion.'],
    'files_sha256': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in sorted(output.iterdir())},
}
(root / 'evidence/core-combined-leap-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('Verified Leap: 405 suites, 335 executed ML cases, 3027 assertions, two installed phases, nine application RPMs')
