# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import runpy
import shutil
import subprocess

root = Path.cwd()
run = root / 'results/node-bundled-headers-check-20261007'
memory = root / 'results/node-bundled-headers-memory-20261007'
status = json.loads((run / 'status.json').read_text())
assert status['exit_code'] == 0
assert status['built_library_sha256_before'] == status['built_library_sha256_after']
recipe = root / 'dependencies/nodejs24-libnode.spec'
spec = recipe.read_text()
# The changelog was added after the check driver took its input snapshot.
# Compare the executable check phase rather than assuming full-file identity.
check = spec.split('%check\n', 1)[1].split('\n%post ', 1)[0]
build = root / 'results/leap-nodejs24-canonical-final-20261007'
image = json.loads((build / 'build.json').read_text())['image']
optflags = subprocess.check_output(
    ['docker', 'run', '--rm', '--network', 'none', image, 'rpm', '--eval', '%{optflags}'],
    text=True).strip()
check = check.replace('%{optflags}', optflags).replace('%{soname}', '137')
check = check.replace('%{_smp_build_ncpus}', '2').replace('%make_build', 'make -j2')
for number, name in re.findall(r'^Source(\d+):\s+(\S+)$', spec, re.M):
    if '://' not in name:
        check = check.replace('%{SOURCE' + number + '}', '/sources/' + name)
assert '%{' not in check
assert (run / 'check.sh').read_text() == 'set -eu\n' + check
text = (run / 'check.log').read_text()
for package in ['libnode-devel', 'abseil-cpp-devel']:
    assert 'package ' + package + ' is not installed' in text
assert '[==========] 192 tests from 31 test suites ran.' in text
assert '[  PASSED  ] 192 tests.' in text
assert len(re.findall(r'^ok \d+ ', text, re.M)) == 5249
assert not re.search(r'^not ok ', text, re.M)
assert len(re.findall(r'^PASS: test/mjsunit/wasm/', text, re.M)) == 31
approval = json.loads((root / 'evidence/node-api-deprecations-20261003.json').read_text())
assert approval['approval']['decision'] == 'accepted'
def normalize(message):
    return message.replace('‘', "'").replace('’', "'")
warnings = re.findall(r'^[^ ]+:\d+:\d+: warning:.*$', text, re.M)
accepted = {normalize(line) for line in approval['diagnostic']['sites']}
assert len(warnings) == 4 and all(normalize(line) in accepted for line in warnings)
tool_logs = ['node-bundled-headers-tools-tests-final-20261007.log',
             'node-bundled-headers-ci-tests-20261007.log']
for name in tool_logs:
    output = (root / 'results' / name).read_text()
    assert re.search(r'Ran 218 tests in [\d.]+s\n\nOK\s*$', output)
negative = root / 'results/node-header-original-negative-20261007.log'
assert 'FAILED (failures=6)' in negative.read_text()
rows = json.loads((memory / 'status.json').read_text())
assert [row['name'] for row in rows] == [
    'platform-priority-control', 'allocation-status-control', 'page-permissions-control']
for row in rows:
    assert row['exit_code'] == 0
    log = (memory / (row['name'] + '.log')).read_text()
    assert 'ERROR SUMMARY: 0 errors' in log
    assert not re.search(r'(?i)warning:|FAIL', log)
    for kind in ['definitely', 'indirectly', 'possibly']:
        assert re.search(kind + r' lost:\s+0 bytes in 0 blocks', log)
    assert re.search(r'still reachable:\s+9,840 bytes in 361 blocks', log)
obs = root / 'results/node-built-library-arm-failure-20261007.log'
assert 'fatal error: absl/synchronization/mutex.h: No such file or directory' in obs.read_text()
out = root / 'evidence/controls/node-bundled-headers-20261008'
out.mkdir(exist_ok=True)
for source, name in [(recipe, 'nodejs24-libnode.spec'),
                     (root / 'tests/test_node_header_inputs.py', 'test_node_header_inputs.py'),
                     (root / 'work/check-node-bundled-headers-20261007.py', 'check.py'),
                     (root / 'work/check-node-bundled-headers-memory-20261007.py', 'check-memory.py'),
                     (Path(__file__), 'record.py'), (run / 'check.sh', 'check.sh'),
                     (run / 'status.json', 'status.json'), (memory / 'status.json', 'memory-status.json'),
                     (negative, negative.name)]:
    shutil.copy2(source, out / name)
for name in tool_logs:
    shutil.copy2(root / 'results' / name, out / name)
logs = [(run / 'check.log', 'check.log.gz'), (obs, 'obs-arm-rev4-failure.log.gz')]
logs += [(memory / (row['name'] + '.log'), row['name'] + '.log.gz') for row in rows]
for source, name in logs:
    (out / name).write_bytes(gzip.compress(source.read_bytes(), mtime=0))
audit = runpy.run_path(str(root / 'work/write-scoped-audit.py'))
passes = {
    9: 'New regression and evidence drivers carry 2026 copyright.',
    53: 'Three omitted include operands now name the bundled headers V8 itself uses. No dependency workaround, suppression or compiler-policy change.',
    54: 'TemporaryDirectory cleanup is registered before fixture setup. Subprocess failures and timeouts propagate; no runtime allocation change.',
    55: 'Every test owns its fixture directory; no shared mutable runtime state is introduced.',
    56: 'Path objects and subprocess argument arrays handle paths with spaces. Tests extract all seven private-header controls from the actual recipe.',
    57: 'Bounded compile-only header probes; no production algorithm or runtime cost change.',
    58: 'Both absent and incompatible installed headers are tested. Negative controls prove each former failure mode; positive controls reject every compiler diagnostic.',
    59: 'Dependency README and RPM changelog explain the missing paths, the masking local dependencies and clean build requirements.',
    61: 'Arguments are passed without shell interpolation. Include-path environment overrides are removed; no credentials or untrusted executable inputs.',
    62: '218 tests pass locally and in pinned CI; original recipe fails six subtests. Complete clean-header RPM check passes 192 native tests, 5249 JavaScript results and 31 Wasm scripts. Three affected Valgrind controls have zero errors or lost allocations; production library hash is unchanged.'
}
audit['write'](out / 'audit.rst', 'Node bundled-header qualification audit',
    'Scope: three RPM private-header corrections, regression coverage for all seven private-header controls, documentation and evidence. '
    '10 Pass, 52 N/A, 0 Fail. No C++ implementation changes. Four retained deprecations match the exact previously approved Node API sites.',
    passes, 'No Qore module, QPP, DataProvider, C++ implementation, Qore test or JAR change in this scope.')
record = {
    'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'Local complete check phase, tool regressions and three affected memory controls pass. Native OBS qualification remains required.',
    'root_cause': 'Three private V8 controls omitted the bundled Abseil directory. V8 mutex.h includes absl/synchronization/mutex.h unconditionally. Installed abseil-cpp-devel masked the missing paths in the local builder; the clean native ARM OBS build failed at Source11.',
    'fix': 'Explicit -Ideps/v8/third_party/abseil-cpp in platform-priority, allocation-status and page-permissions controls. All seven private V8 controls now select the bundled headers.',
    'validation': {
        'tool_tests_local': 218, 'tool_tests_pinned_ci': 218, 'private_header_consumers': 7,
        'original_recipe_expected_subtest_failures': 6, 'native_tests': 192,
        'javascript_reported_results_including_upstream_skips': 5249, 'wasm_scripts': 31,
        'valgrind_controls': 3, 'memory_errors': 0, 'lost_allocations': 0,
        'reachable_openssl_startup_bytes_per_control': 9840,
        'production_library_sha256': status['built_library_sha256_after'],
        'reviewed_deprecations': warnings, 'approval': 'evidence/node-api-deprecations-20261003.json'
    },
    'limits': [
        'The complete modified check phase reuses the qualified canonical compiled source tree. It removes libnode-devel, abseil-cpp-devel and the dependent protobuf-devel from the disposable container before compiling any controls.',
        'All three memory controls use the newly compiled binaries and versioned library. OpenSSL retains 361 reachable startup allocations; no definite, indirect or possible losses and no suppressions.',
        'The driver captured the spec before its changelog addition. The exact expanded current check phase is byte-identical to the executed check.sh.',
        'No native OBS success is inferred from local x86_64 qualification. Both native architectures still need the new committed source revision.'
    ],
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
}
(root / 'evidence/node-bundled-headers-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('Node bundled-header correction qualified and audited locally')
