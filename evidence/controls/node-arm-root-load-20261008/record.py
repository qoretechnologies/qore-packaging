# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import re
import shutil
import subprocess

root = Path.cwd()
source = root / 'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
run = root / 'work/node-arm-root-load-20261008'
out = root / 'evidence/controls/node-arm-root-load-20261008'
out.mkdir(parents=True, exist_ok=True)
status = json.loads((run / 'status.json').read_text())
assert len(status) == 6 and all(row['exit_code'] == 0 for row in status)
extracts = json.loads((run / 'source-extracts.json').read_text())
control = (run / 'control.cc').read_text()
for row in extracts:
    assert row['text'] in (source / row['file']).read_text()
    assert row['text'] in control
    assert hashlib.sha256(row['text'].encode()).hexdigest() == row['sha256']

qualification = []
for mode, count, rejected in [('release', 627, 0), ('debug', 641, 14)]:
    compiler = (run / (mode + '-compile.log')).read_text()
    warnings = [line for line in compiler.splitlines() if 'warning:' in line]
    if mode == 'release':
        assert len(warnings) == 1 and '‘index_constant’ may be used uninitialized [-Wmaybe-uninitialized]' in warnings[0]
        for step in ['Constant::FitsInInt32()', 'InstructionSelectorT::AddImmediate', 'Arm64OperandGeneratorT::UseImmediate64', 'EmitLoad']:
            assert step in compiler
    else:
        assert not compiler
    normal = f'PASS: {count} root-load checks; {rejected} invalid root-index cases rejected\n'
    assert (run / (mode + '-normal.log')).read_text() == normal
    vg = (run / (mode + '-valgrind.log')).read_text()
    assert normal in vg and 'ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)' in vg
    assert 'All heap blocks were freed -- no leaks are possible' in vg
    qualification.append({'mode': mode, 'checks': count, 'invalid_root_indexes_rejected': rejected,
                          'warning_reproduced': mode == 'release', 'normal_exit': 0,
                          'valgrind_exit': 0, 'valgrind_errors': 0, 'all_allocations_freed': True})

# Current producer inventory, including forwarding factories and legacy graph conversion.
reviews = {
 'compiler/graph-assembler.cc': 'Factory creates the root-register operation; Load(type, object, int offset) materializes IntPtrConstant(offset).',
 'compiler/graph-assembler.h': 'Declares both graph-index and integer-offset overloads; declaration alone supplies no dynamic root index.',
 'compiler/raw-machine-assembler.h': 'LoadProtectedPointerFromObject loads trusted_cage_base through an IntPtrConstant; its dynamic object offset applies to the object, not the root-register load. The other occurrence is the factory.',
 'compiler/code-assembler.cc': 'The two root wrappers forward their offset. LoadUint8FromRootRegister has one call, with IntPtrConstant(is_on_central_stack_flag_offset()).',
 'compiler/code-assembler.h': 'Declarations of the two forwarding wrappers; callers are inventoried separately.',
 'builtins/wasm.tq': 'The sole LoadPointerFromRootRegister call uses constexpr kThreadInWasmFlagAddressOffset, generated from Isolate::thread_in_wasm_flag_address_offset().',
 'compiler/fast-api-calls.cc': 'PropagateException loads an integer BuiltinSlotOffset; the other root load uses root_slot_offset(kTheHoleValue).',
 'compiler/wasm-compiler.cc': 'BuildLoadIsolateRoot returns a constant or the root-register operation. Its users load root_slot_offset, integer BuiltinSlotOffset or thread_in_wasm_flag_address_offset. The direct context root operation is used for a store.',
 'compiler/machine-operator.h': 'Operator declaration; no producer index.',
 'compiler/wasm-gc-lowering.cc': 'Null loads a constant root_slot_offset; external string data passes the root to BuildLoadExternalPointerFromObject, whose helper loads fixed pointer-table fields before dynamic table indexing.',
 'compiler/wasm-graph-assembler.cc': 'Sandbox external/trusted pointer helpers load fixed IsolateData table-field offsets. Handle-derived dynamic offsets use the loaded table pointer, never the root-register operation as base.',
 'compiler/turboshaft/growable-stacks-reducer.h': 'Root load uses integer IsolateData::jslimit_offset().',
 'compiler/turboshaft/stack-check-lowering-reducer.h': 'Root load uses integer IsolateData::jslimit_offset().',
 'compiler/turboshaft/variable-reducer.h': 'Preserves a root-register operation when merging a variable containing that same root register; does not add load indexes.',
 'compiler/backend/instruction-selector.cc': 'VisitLoadRootRegister is UNREACHABLE: the root operator is consumed by offset loads/stores, not emitted as a generic register-producing instruction.',
 'compiler/turboshaft/wasm-assembler-helpers.h': 'Both root-load branches use integer IsolateData::root_slot_offset(index); index is a C++ RootIndex at graph construction, not a runtime graph node.',
 'compiler/turboshaft/wasm-in-js-inlining-reducer-inl.h': 'Root load uses integer thread_in_wasm_flag_address_offset().',
 'compiler/turboshaft/wasm-lowering-reducer.h': 'RootConstant uses integer root_slot_offset(index) in both endian branches.',
 'compiler/turboshaft/memory-optimization-reducer.h': 'External-pointer decoding loads fixed table-field offsets from the root, then applies the dynamic handle index to the loaded table pointer.',
 'compiler/turboshaft/graph-builder.cc': 'Converts the legacy kLoadRootRegister operation to ReduceLoadRootRegister without changing its consumers.',
 'compiler/turboshaft/assembler.h': 'Trusted-pointer helper loads a constant table-base field before dynamic table indexing. Load(base, kind, representation, int32 offset) passes Nullopt index and the integer offset. The other occurrence is the root factory.',
 'wasm/turboshaft-graph-interface.cc': 'Loads integer CEntry BuiltinSlotOffset, thread flag-address and exception offsets. Other root-register occurrences are stores of DataView error type or context.',
 'wasm/wrappers.cc': 'Loads integer thread flag-address, central-stack SP/limit, on-central-stack flag and real-jslimit offsets. Other root occurrences are stores. Dynamic StackMemory fields use a separately loaded object pointer.',
}
inventory = []
for path in sorted((source / 'deps/v8/src').rglob('*')):
    if not path.is_file() or path.suffix not in {'.h', '.cc', '.tq'}:
        continue
    content = path.read_text()
    lines = content.splitlines()
    for number, line in enumerate(lines, 1):
        if re.search(r'LoadRootRegister\(', line):
            rel = str(path.relative_to(source / 'deps/v8/src'))
            assert rel in reviews, (rel, number, line)
            inventory.append({'path': str(path.relative_to(source)), 'line': number, 'text': line,
                              'context': '\n'.join(lines[max(0, number - 6):number + 20]),
                              'review': reviews[rel]})
assert len(inventory) == 40, len(inventory)
review_files = set('deps/v8/src/' + name for name in reviews)
review_files.update(row['file'] for row in extracts)
review_files.add('deps/v8/src/compiler/turboshaft/machine-optimization-reducer.h')
source_review = {'root_occurrences': inventory, 'file_reviews': reviews,
                'files_sha256': {name: hashlib.sha256((source / name).read_bytes()).hexdigest() for name in sorted(review_files)}}
# Preserve source contexts of the forwarding wrappers and simplifier configuration.
source_review['wrapper_inventory'] = subprocess.check_output(
    ['rg', '-n', '-C', '5', 'LoadPointerFromRootRegister|LoadUint8FromRootRegister|BuildLoadIsolateRoot', 'deps/v8/src'],
    cwd=source, text=True)
(out / 'producer-review.json').write_text(json.dumps(source_review, indent=2) + '\n')

raw = (root / 'results/node-native-rev5-live-20261008/aarch64.log').read_text()
diagnostic = '../deps/v8/src/compiler/backend/instruction.h:1251:58: warning: ‘index_constant’ may be used uninitialized [-Wmaybe-uninitialized]'
assert raw.count(diagnostic) == 1
lines = raw.splitlines()
at = next(i for i, line in enumerate(lines) if diagnostic in line)
(out / 'native-warning.log.gz').write_bytes(gzip.compress(('\n'.join(lines[at-7:at+10]) + '\n').encode(), mtime=0))
for path in run.iterdir():
    if path.suffix == '.log':
        (out / (path.name + '.gz')).write_bytes(gzip.compress(path.read_bytes(), mtime=0))
    elif path.suffix in {'.json', '.cc', '.py'} or path.name == 'V8-LICENSE':
        shutil.copy2(path, out / path.name)
shutil.copy2(root / 'work/prepare-node-arm-root-load-20261008.py', out / 'prepare.py')
shutil.copy2(Path(__file__), out / 'record.py')
spec = importlib.util.spec_from_file_location('audit', root / 'work/write-scoped-audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
passes = {
 9: 'New control and evidence carry 2026 copyright; copied V8 implementation retains its BSD license.',
 53: 'No production changes, suppression or compiler-flag changes. The user approved this exact retained diagnostic on 2026-10-08.',
 54: 'Stack-owned graph and emitter adapters unwind the test-only rejection exception; both Valgrind runs free all allocations.',
 55: 'Single-threaded controls; no production shared state is changed.',
 56: 'Typed graph tags, enums, fixed-width constants and checked output records. Nonintegral constants leave the matcher output untouched.',
 57: 'Bounded branch/boundary matrix; production performance is unchanged.',
 58: 'Debug rejects all 13 nonintegral kinds and a dynamic root index before emitting. Invalid Release root indexes are deliberately not executed or claimed as supported.',
 59: 'Evidence records current producer review, exact source extracts, warning call chain, test commands and adapter limits.',
 61: 'Offline container, fixed inputs, bounds-checked graph/emitter arrays; no external writes or credentials.',
 62: 'All 1268 normal checks pass; both Valgrind runs report zero errors and all allocations freed. The Release control reproduces the exact source-variable warning.'
}
audit.write(out / 'audit.rst', 'V8 ARM root-load compiler diagnostic review',
            'All 62 checks: 10 Pass, 52 N/A, 0 Fail. The user approved this exact diagnostic on 2026-10-08; native RPM qualification remains open.',
            passes, 'No Qore modules, QPP, DataProviders, JNI or public API changes. Finite standalone controls are outside a cancellable Qore program; no production I/O or loops change.')
record = {
 'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
 'status': 'Current source invariant and controls qualified; exact diagnostic approved by the user on 2026-10-08.',
 'diagnostic': diagnostic,
 'source_proof': [
  'MatchSignedIntegralConstant initializes index_constant for Word32 and Word64. All general/external-base uses guard its boolean result. The root-register branch instead relies on DCHECK(is_index_constant).',
  'All 40 current LoadRootRegister occurrences were classified, including factories, declarations, forwarding wrappers and stores. Current root-load producers supply integer isolate-field/root-slot/builtin offsets. Runtime pointer-table indexes apply to the loaded table pointer, not to the root register.',
  'ARM LoadStoreSimplificationConfiguration sets kMinOffset=1 and kMaxOffset=0, forcing even offset zero into an index. An absent index becomes IntPtrConstant(offset); existing integer constants stay or are constant-folded. The unchanged simplifier control verifies raw producer offsets through the full int32 boundaries.',
  'The compiler cannot infer the producer invariant from the independent base/index graph tags after DCHECK is compiled out. The exact FitsInInt32 -> AddImmediate -> UseImmediate64 -> EmitLoad warning reproduces in Release; Debug checks reject unsupported root indexes.',
  'VisitLoadRootRegister itself is UNREACHABLE; fabricating a dynamic root-register load violates the current graph contract. A generic-register fallback would not be a justified source fix.'
 ],
 'qualification': qualification,
 'coverage': ['Word32/Word64 signed boundaries, 32-bit sign extension and optional output override.',
              'Raw root integer offsets through unchanged ARM simplifier, including atomic-kind handling and int32 endpoints.',
              'External-reference root-relative signed-32-bit boundaries, permission denial and fallback, without overflowing signed addition.',
              'General constant/immediate/register loads and modeled dynamic/shift addressing.',
              'All 15 ConstantOp kinds; 13 nonintegral matcher rejections preserve the sentinel. Debug additionally rejects those root indexes and one dynamic index before emission.'],
 'approval': {'state': 'approved', 'date': '2026-10-08', 'user_response': 'Allow this exact diagnostic', 'scope': 'Only this index_constant/FitsInInt32 warning from ARM64 EmitLoad in the reviewed Node 24.18.1 sources. No suppression or flags change.'},
 'limits': ['Host GCC 13 control models ARM instruction selection, not ARM instruction execution. Full native build/runtime qualification remains required.',
            'Exact upstream matcher, signed-integral accessor, FitsInInt32, immediate wrappers, full EmitLoad and simplifier bodies are unchanged. Graph storage, immediate collection and emission are typed adapters.',
            'CanBeImmediate models the selected 8-bit-load immediate interval; TryMatchLoadStoreShift models one shifted form. Other instruction encodings and shift matching are not qualified by this control.',
            'Simplifier coverage is the untagged integer-offset producer path; adapter-only tagged-base and general graph-optimization behavior is not claimed.',
            'Source proof is bounded to the recorded current producers. A future dynamic root-register index requires revisiting this conclusion. Unsupported Release inputs are not executed; Debug rejection does not imply Release hardening.',
            'No blanket uninitialized-variable exception; no warning filtering, source initialization workaround or compiler-policy change.'],
 'files_sha256': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(out.iterdir())}
}
(root / 'evidence/node-arm-root-load-diagnostic-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('Qualified root-load control:', len(inventory), 'source occurrences;', len(record['files_sha256']), 'evidence files; exact diagnostic approved')
