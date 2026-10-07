# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import runpy
import shutil

root = Path.cwd()
run = root / 'results/node-built-library-check-20261007'
status = json.loads((run / 'status.json').read_text())
assert status['exit_code'] == 0
assert status['built_library_sha256_before'] == status['built_library_sha256_after']
recipe = root / 'dependencies/nodejs24-libnode.spec'
assert hashlib.sha256(recipe.read_bytes()).hexdigest() == status['recipe_sha256']
text = (run / 'check.log').read_text()
assert 'package libnode-devel is not installed' in text
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
for name in ('node-built-library-tools-tests-20261007.log', 'node-built-library-ci-tests-20261007.log'):
    output = (root / 'results' / name).read_text()
    assert re.search(r'Ran 214 tests in [\d.]+s\n\nOK\s*$', output)
obs = root / 'results/node-native-x86_64-rev3-20261007.log'
assert 'cannot find -lnode' in obs.read_text()
out = root / 'evidence/controls/node-built-library-20261007'
out.mkdir(exist_ok=True)
for source, dest in [(recipe, 'nodejs24-libnode.spec'),
                     (root / 'tests/test_node_link_inputs.py', 'test_node_link_inputs.py'),
                     (root / 'work/check-node-built-library-20261007.py', 'check.py'),
                     (Path(__file__), 'record.py'),
                     (run / 'check.sh', 'check.sh'), (run / 'status.json', 'status.json')]:
    shutil.copy2(source, out / dest)
for name in ('node-built-library-tools-tests-20261007.log', 'node-built-library-ci-tests-20261007.log',
             'node-built-library-obs-before-20261007.xml'):
    shutil.copy2(root / 'results' / name, out / name)
for source, name in [(run / 'check.log', 'check.log.gz'), (obs, 'obs-rev3-failure.log.gz')]:
    (out / name).write_bytes(gzip.compress(source.read_bytes(), mtime=0))
audit = runpy.run_path(str(root / 'work/write-scoped-audit.py'))
passes = {
    9: 'New regression and evidence controls carry 2026 copyright.',
    53: 'The recipe names the actual built ELF file; no extra dependency, symlink workaround, flag change or suppression.',
    54: 'Test temporary directories use deterministic cleanup; subprocess failures and timeouts propagate. No runtime allocation changes.',
    55: 'Every test owns its fixture directory; no shared mutable runtime state is introduced.',
    56: 'Path objects and subprocess argument arrays avoid shell interpolation. Every recipe operand is read and exercised.',
    57: 'Nine bounded native link inputs; no production algorithm or runtime cost changes.',
    58: 'Missing built libraries fail even if an installed development copy is available. Compiler warnings fail the unit controls.',
    59: 'Dependency README and RPM changelog explain the versioned-only build and the installed-library fallback regression.',
    61: 'Commands use argument arrays; private temporary paths include spaces. Inherited loader/compiler search overrides are removed.',
    62: 'All 214 tool tests pass locally and in the pinned CI image. Complete RPM check passes after removing libnode-devel: 192 native tests, 5249 reported JavaScript results and 31 Wasm scripts. Production library hash is unchanged.'
}
audit['write'](out / 'audit.rst', 'Node native control link-input audit',
    'Scope: nine RPM native-control link operands, their regression and documentation. '
    '10 Pass, 52 N/A, 0 Fail. No C++ implementation changes. Four retained compiler '
    'deprecations match the exact previously approved Node API sites.', passes,
    'No Qore module, QPP, DataProvider, C++ implementation, Qore test or JAR change in this scope.')
record = {
    'schema': 1, 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.', 'date': '2026-10-07',
    'status': 'Local complete RPM check and package-tool regressions pass. Corrected canonical OBS upload and native qualification remain required.',
    'root_cause': 'Node creates out/Release/libnode.so.137 without libnode.so. Eight -lnode controls therefore failed in clean OBS. The local builder had libnode-devel installed, which satisfied those link operands; runtime rpath still selected the freshly built versioned library.',
    'fix': 'All nine native shared-library controls link out/Release/libnode.so.%{soname} directly, including the inspector control formerly using -l:libnode.so.%{soname}. Missing output cannot fall back to a host library.',
    'validation': {'tool_tests_local': 214, 'tool_tests_pinned_ci_image': 214,
        'native_link_operands_covered': 9, 'native_tests': 192,
        'javascript_reported_results_including_upstream_skips': 5249, 'wasm_scripts': 31,
        'installed_development_library_removed': True,
        'production_library_sha256': status['built_library_sha256_after'],
        'reviewed_deprecations': warnings, 'approval': 'evidence/node-api-deprecations-20261003.json'},
    'limits': ['This reuses the qualified canonical compiled library and reruns the entire modified check phase without an installed Node development package.',
               'Native OBS x86_64 and aarch64 builds still must pass; no native OBS success is inferred from this local result.',
               'No C++ source changed, so no new Valgrind run is required for the link-recipe correction. Canonical implementation memory evidence remains in node-canonical-final-20261007.json.',
               'The four compiler messages differ from the recorded approved messages only in locale-dependent quotation marks.'],
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
}
(root / 'evidence/node-built-library-20261007.json').write_text(json.dumps(record, indent=2) + '\n')
print('Node link-input correction fully qualified and audited locally')
