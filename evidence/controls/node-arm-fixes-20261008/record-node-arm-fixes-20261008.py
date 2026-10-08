# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import re
import shutil

root = Path.cwd()
out = root / 'evidence/controls/node-arm-fixes-20261008'
out.mkdir()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def read_run(name):
    path = root / 'results' / (name + '-20261008')
    return path, json.loads((path / 'status.json').read_text())

header, hs = read_run('node-arm-header')
assert [s['exit_code'] for s in hs] == [1, 0]
assert "inline function 'v8::internal::Operand::Operand(T) [with T = int]' used but never defined" in (header / 'original.log').read_text()
assert not (header / 'fixed.log').read_text()
codegen, cs = read_run('node-arm-header-codegen')
assert all(s['exit_code'] == 0 for s in cs)
assert (codegen / 'original-code.o').read_bytes() == (codegen / 'fixed-code.o').read_bytes()
assert (codegen / 'original.log').read_bytes() == (codegen / 'fixed.log').read_bytes()
assert (codegen / 'fixed.log').read_text().count('warning:') == 1
assert 'CheckSpecialClassRanges' in (codegen / 'fixed.log').read_text()
package, ps = read_run('node-arm-package-control')
assert [s['exit_code'] for s in ps] == [1, 0, 0]
assert (package / 'fixed.log').read_text() == 'PASS: 4491 actual ARM64 Operand checks\n'
for path in (package / 'valgrind.log', codegen / 'operand-valgrind.log'):
    text = path.read_text()
    assert 'PASS: 4491 actual ARM64 Operand checks' in text
    assert 'ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)' in text
    assert 'All heap blocks were freed' in text
zlib, zs = read_run('node-arm-zlib')
assert len(zs) == 14 and all(s['exit_code'] == 0 for s in zs)
zlib_hashes = {}
for p in zlib.glob('*-original-code.o'):
    name = p.name.removesuffix('-original-code.o')
    fixed = zlib / (name + '-fixed-code.o')
    assert p.read_bytes() == fixed.read_bytes()
    assert not (zlib / (name + '-fixed.log')).read_text()
    original = (zlib / (name + '-original.log')).read_text()
    if name in ('generic-neon', 'generic-neon-alt'):
        assert original.count('warning:') == 1 and '_cpu_check_features' in original
    else:
        assert not original
    zlib_hashes[name] = sha(p)
assert len(zlib_hashes) == 7
platforms, plats = read_run('node-arm-zlib-platforms')
assert len(plats) == 2 and all(s['exit_code'] == 0 for s in plats)
preprocessor = json.loads((platforms / 'comparison.json').read_text())
cases = json.loads((platforms / 'cases.json').read_text())
assert len(cases) == 48 and preprocessor['preprocessed_sources_identical']
for case in cases:
    assert (platforms / ('original-' + case['name'] + '.i')).read_bytes() == (platforms / ('fixed-' + case['name'] + '.i')).read_bytes()
tool_log = (root / 'results/node-arm-source-tools-tests-20261008.log').read_text()
assert re.search(r'Ran 223 tests in [\d.]+s\n\nOK\s*$', tool_log)
source = root / 'results/node-arm-source-final-20261008'
verification = json.loads((source / 'verification.json').read_text())
assert verification['patches'] == 24 and verification['new_patches_zero_offset']
regexp = json.loads((root / 'evidence/node-arm-regexp-diagnostic-20261008.json').read_text())
for name, digest in regexp['files_sha256'].items():
    assert sha(root / name) == digest, name
assert regexp['approval']['basis'] == 'existing user-approved policy; no new user response is claimed'

def retain(path, relative):
    target = out / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix in ('.log', '.i', '.o'):
        target = target.with_name(target.name + '.gz')
        target.write_bytes(gzip.compress(path.read_bytes(), mtime=0))
    else:
        shutil.copy2(path, target)

for directory in (header, codegen, package, zlib, platforms):
    for p in sorted(directory.rglob('*')):
        if p.is_symlink() or not p.is_file():
            continue
        if p.suffix in ('.log', '.json', '.cc', '.h', '.py', '.i') or p.name.endswith('-code.o') or p.name == 'regexp-macro-assembler-arm64.o.d':
            retain(p, directory.name + '/' + str(p.relative_to(directory)))
for name in ['verification.json', 'patches.log', 'x86_64.spec', 'aarch64.spec']:
    retain(source / name, 'source/' + name)
retain(root / 'results/node-arm-source-20261008/patches.log', 'source/initial-validation-patches.log')
retain(root / 'results/node-arm-source-20261008/prepare.log', 'source/prepare.log')
retain(root / 'results/node-arm-source-tools-tests-20261008.log', 'tools-tests.log')
for name in ['check-node-arm-header-20261008.py', 'check-node-arm-header-codegen-20261008.py',
             'check-node-arm-package-control-20261008.py', 'check-node-arm-zlib-20261008.py',
             'check-node-arm-zlib-platforms-20261008.py', 'prepare-node-arm-fixes-20261008.py',
             'record-node-arm-fixes-20261008.py']:
    retain(root / 'work' / name, name)
for name in ['nodejs24-libnode.spec', 'nodejs24-libnode.rst', 'nodejs24-arm-header-operand.patch',
             'nodejs24-arm-cpu-feature-guard.patch', 'nodejs24-arm-header-test.py', 'nodejs24-arm-operand-test.cc']:
    retain(root / 'dependencies' / name, name)
retain(root / 'tests/test_node_arm_header.py', 'test_node_arm_header.py')
retain(root / 'work/nodejs24-libnode-arm-fixes-candidate-20261008/source-manifest.json', 'source-manifest.json')
canonical = root / 'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
retain(canonical / 'deps/v8/LICENSE', 'V8-LICENSE')
for relative in verification['qualified_source_sha256']:
    retain(source / 'source' / relative, 'fixed/' + relative)
    retain(canonical / relative, 'original/' + relative)

loader = importlib.util.spec_from_file_location('audit', root / 'work/write-scoped-audit.py')
audit = importlib.util.module_from_spec(loader)
loader.loader.exec_module(audit)
passes = {
  9: 'All new package controls, patches and evidence scripts carry 2026 copyright; verbatim upstream material retains its license.',
  17: 'The production C/C++ patches add no filesystem operations. The Python test writes only explicit build-output paths.',
  18: 'The production patches and controls add no network access; local controls run in network-disabled containers.',
  24: 'Both production changes select existing expressions/declarations and add no blocking operation.',
  53: 'Root causes are fixed at the unavailable inline default argument and the missing platform guard. No runtime flags, retry, suppression or fallback changes. The unchanged exhaustive-enum diagnostic is reviewed under the existing approved policy.',
  54: 'Operand values have automatic storage; changes add no owned allocations. Python subprocess failures terminate qualification. Both final native control runs free every allocation under Valgrind.',
  55: 'No mutable production state or synchronization changes. Controls run single-threaded in separate disposable containers with read-only source overlays.',
  56: 'The explicit call uses the same int Operand constructor as the former default. Real Operand accessors verify tags before variant fields; compiler receipt validation rejects other architectures and malformed commands.',
  57: 'The complete ARM-target regexp object and seven CPU-feature objects remain byte-identical after removing non-runtime metadata. No production work is added.',
  58: 'Original-header negative control fails exactly at the missing inline definition. Both generic NEON spellings reproduce the unused helper. New helper rejects malformed and foreign-architecture receipts; subprocess exit codes are enforced.',
  59: 'Dependency guide and spec changelog explain both fixes, native per-build checks and host/SDK qualification limits. No public API changes.',
  61: 'Compiler commands are tokenized and passed directly without a shell. Negative tests preserve literal shell characters and reject unexpected command shapes. No credentials, user input or new production buffer accesses.',
  62: '4491 actual Operand checks pass normally and under Valgrind. Seven code/data identities, 48 preprocessing identities, 223 tool tests, complete 24-patch source verification and both recipe architectures pass. Native ARM execution remains an explicit open delivery gate.',
}
audit.write(out / 'audit.rst', 'Node ARM declaration fixes audit',
    'Scope: two private upstream source fixes, native RPM regressions, package recipe and retained qualification. All 62 checks: 13 Pass, 49 N/A, 0 Fail. Native ARM build and installed-package execution remain required.',
    passes, 'No corresponding Qore module, QPP, DataProvider, JNI or Qore-language test change. Production changes add no iteration or cancellation point; bounded standalone controls do not execute inside a Qore program.')
record = {
    'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'Two ARM declaration defects fixed and locally qualified; native ARM build and installed-package gates remain required.',
    'root_causes': ['The regexp header constructs a default Operand without including its inline constructor definition.',
                    'Generic NEON configuration compiles an empty private CPU helper even though no platform caller is selected.'],
    'fixes': ['Move the identical zero Operand expression to the sole previously implicit implementation call.',
              'Compile the private helper only for the five platforms selecting its caller; retain the outer architecture dispatch.'],
    'qualification': {'operand_checks_per_execution': 4491, 'valgrind_errors': 0, 'all_allocations_freed': True,
                      'complete_regexp_object_identical': sha(codegen / 'fixed-code.o'),
                      'cpu_feature_object_identities': zlib_hashes, 'preprocessor_controls': preprocessor,
                      'packaging_tests': 223, 'source_verification': verification},
    'existing_approval': 'evidence/node-arm-regexp-diagnostic-20261008.json',
    'limits': ['Local controls compile V8 ARM target types on x86_64; they do not execute native ARM instructions.',
               'The one host-unsupported ARM branch-protection compiler flag is removed only from local adapted controls; the native RPM helper retains its actual receipt flags.',
               'Standalone control compilation omits LTO; production compiler flags and LTO are unchanged.',
               'The complete regexp control retains only the separately reviewed exhaustive-enum warning covered by the existing approved policy.',
               'Initial source validation wrongly expected zero offsets in all historical patches. The sole existing timezone patch offset was verified by full source identity against the qualified canonical build; no patch was changed to accommodate it.',
               'The live complete Node check uses the preceding fixture-fix recipe. It does not qualify these ARM source changes.'],
    'files_sha256': {str(p.relative_to(root)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()},
}
(root / 'evidence/node-arm-fixes-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('Recorded ARM fixes, qualified source identities, controls and all 62 audit checks.')
