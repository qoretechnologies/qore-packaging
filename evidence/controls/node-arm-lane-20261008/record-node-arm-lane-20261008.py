# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import shutil

root = Path.cwd()
run = root / 'work/node-arm-lane-control-20261008'
out = root / 'evidence/controls/node-arm-lane-20261008'
out.mkdir()
source = root / 'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
status = json.loads((run / 'status.json').read_text())
assert len(status) == 6 and all(s['exit_code'] == 0 for s in status)
for mode in ['release', 'debug']:
    log = (run / (mode + '-compile.log')).read_text()
    assert log.count('warning:') == 1 and 'control reaches end of non-void function [-Wreturn-type]' in log
    assert (run / (mode + '-normal.log')).read_text() == 'PASS: 9 declared SIMD lane kinds map to their correct machine representations\n'
    log = (run / (mode + '-valgrind.log')).read_text()
    assert 'ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)' in log
    assert 'All heap blocks were freed' in log
assert json.loads((run / 'runtime-status.json').read_text())['exit_code'] == 0
runtime = json.loads((run / 'runtime.stdout').read_text())
assert runtime == {'node': 'v24.18.1', 'arch': 'x64', 'kinds': 9, 'checks': 426, 'result': 'pass'}
assert not (run / 'runtime.stderr').read_text()
for row in json.loads((run / 'source-extracts.json').read_text()):
    assert row['text'] in (source / row['file']).read_text()
    assert hashlib.sha256(row['text'].encode()).hexdigest() == row['sha256']
for p in run.iterdir():
    if p.name in ['release', 'debug']:
        continue
    if p.suffix == '.log':
        (out / (p.name + '.gz')).write_bytes(gzip.compress(p.read_bytes(), mtime=0))
    else:
        shutil.copy2(p, out / p.name)
for name in ['prepare-node-arm-lane-control-20261008.py', 'record-node-arm-lane-20261008.py']:
    shutil.copy2(root / 'work' / name, out / name)
paths = ['deps/v8/src/wasm/turboshaft-graph-interface.cc',
         'deps/v8/src/compiler/turboshaft/graph-builder.cc',
         'deps/v8/src/compiler/turboshaft/assembler.h',
         'deps/v8/src/compiler/turboshaft/int64-lowering-reducer.h',
         'deps/v8/src/compiler/turboshaft/machine-optimization-reducer.h']
review = []
for path in paths:
    text = (source / path).read_text().splitlines()
    hits = [i for i, line in enumerate(text) if 'Simd128ExtractLane(' in line or 'ReduceSimd128ExtractLane' in line]
    review.append({'file': path, 'sha256': hashlib.sha256((source / path).read_bytes()).hexdigest(),
                   'excerpts': [{'line': i+1, 'text': '\n'.join(text[max(0, i-3):i+5])} for i in hits]})
(out / 'producer-review.json').write_text(json.dumps(review, indent=2) + '\n')
loader = importlib.util.spec_from_file_location('audit', root / 'work/write-scoped-audit.py')
audit = importlib.util.module_from_spec(loader)
loader.loader.exec_module(audit)
passes = {
  9: 'New controls and evidence scripts carry 2026 copyright; upstream source and V8 license are preserved.',
  53: 'The unchanged exhaustive enum method is reviewed under the existing approved V8 return-type policy. No runtime source, compiler flag, warning suppression or fallback changes.',
  54: 'C++ control owns only stack objects; both Valgrind runs free all allocations. JavaScript assertion failures terminate the standalone control.',
  55: 'Controls are single-threaded; no mutable production state or synchronization changes.',
  56: 'The exact uint8_t Kind and MachineRepresentation declarations and method are preserved. Expected output is an independent table covering every declared Kind.',
  57: 'Qualification adds no production cost. All nine distinct enum mappings are checked without redundant repeated stress loops.',
  58: 'Actual Wasm tests reject both first-invalid and 255 lane indices for every opcode; valid exports are checked across six distinct data patterns.',
  59: 'Evidence records producer invariants, exact compiler warning, runtime flags, adapter boundaries and missing native ARM execution.',
  61: 'Source paths and command arrays are explicit. Actual Wasm invalid lane boundaries are rejected before execution; no credentials or external network access.',
  62: 'Every declared enum value passes in both compiler modes and under Valgrind. The warning reproduces in both modes. Actual optimized x86_64 Wasm passes 408 result comparisons and 18 negative boundary checks.',
}
audit.write(out / 'audit.rst', 'V8 SIMD lane-dispatch diagnostic audit',
    'Scope: unchanged method reproduction, producer review and standalone controls. All 62 checks: 10 Pass, 52 N/A, 0 Fail. Native ARM runtime and full package gates remain required.',
    passes, 'No Qore module, QPP, DataProvider, JNI, public API or Qore test changes. No production I/O, loops or blocking operations are added.')
record = {'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
    'status': 'Reviewed exhaustive-enum diagnostic qualified under existing policy; native ARM runtime remains required.',
    'diagnostic': '../deps/v8/src/compiler/turboshaft/operations.h:8002:3: warning: control reaches end of non-void function [-Wreturn-type]',
    'function': 'Simd128ExtractLaneOp::element_rep(Kind)',
    'root_cause': 'All nine fixed-underlying-type enum members return. GCC also considers unnamed uint8_t values, which the reviewed graph producers do not generate.',
    'producer_invariants': ['Wasm and legacy graph builders select only named enum constants for validated lane opcodes.',
                            'Assembler and machine-optimization reducers forward the existing Kind unchanged.',
                            'Int64 lowering either forwards Kind or selects the named I32x4 variant.'],
    'qualification': {'native_declared_kinds_per_run': 9, 'native_runs': 4, 'compiler_modes': ['release', 'debug'],
                      'valgrind_errors': 0, 'all_allocations_freed': True, 'actual_node_x86_64': runtime},
    'approval': {'basis': 'existing user-approved V8 exhaustive-enum policy; no new user response is claimed',
                 'evidence': 'evidence/node-gcc-return-policy-proposal-20261006.json'},
    'limits': ['The native control uses exact enum declarations and unchanged static method; the containing operation base class is omitted because it has no role in this static mapping.',
               'Actual Wasm execution is x86_64, with Liftoff/lazy compilation disabled and experimental fp16 enabled for the control only. Production defaults are unchanged.',
               'On hardware without native fp16 the upstream runtime uses its I16 extraction/conversion fallback. The static F16 mapping is separately covered; runtime results do not prove that hardware branch executed.',
               'Unnamed enum values are excluded by producer invariants, not executed through undefined C++ fallthrough.',
               'Native ARM package runtime and remaining diagnostics must still be qualified before publication.'],
    'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}}
(root / 'evidence/node-arm-lane-diagnostic-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('Qualified all nine SIMD kinds and 426 actual Wasm checks under the existing enum policy.')
