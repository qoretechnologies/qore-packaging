# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import re
import shutil

root=Path.cwd()
run=root/'work/node-arm-memory-control-20261008'
out=root/'evidence/controls/node-arm-memory-20261008'
out.mkdir()
source=root/'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
status=json.loads((run/'status.json').read_text())
assert len(status)==18 and all(row['exit_code']==0 for row in status)
records=[]
for compression,sandbox in [(0,0),(1,0),(1,1)]:
    for mode in ['release','debug']:
        stem=f'{mode}-c{compression}-s{sandbox}'
        log=(run/(stem+'-compile.log')).read_text()
        warnings=[line for line in log.splitlines() if 'warning:' in line]
        assert len(warnings)==3 and all('control reaches end of non-void function [-Wreturn-type]' in line for line in warnings),warnings
        normal=(run/(stem+'-normal.log')).read_text()
        match=re.fullmatch(r'PASS: 451 selector cases \((\d+) rejected\)\n',normal)
        assert match,normal
        vg=(run/(stem+'-valgrind.log')).read_text()
        assert 'ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)' in vg
        assert 'All heap blocks were freed' in vg and normal in vg
        records.append({'mode':mode,'pointer_compression':bool(compression),'sandbox':bool(sandbox),
                        'cases_per_execution':451,'rejected_per_execution':int(match[1]),
                        'normal_exit':0,'valgrind_exit':0,'compiler_diagnostics':3})
for row in json.loads((run/'source-extracts.json').read_text()):
    assert row['text'] in (source/row['file']).read_text()
    assert hashlib.sha256(row['text'].encode()).hexdigest()==row['sha256']
for p in run.iterdir():
    if p.suffix=='.log':
        (out/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
    elif p.suffix in ['.json','.cc','.py'] or p.name=='V8-LICENSE':
        shutil.copy2(p,out/p.name)
initial=root/'work/node-arm-memory-control-initial-20261008/release-c0-s0-compile.log'
(out/'initial-release-unused-parameter.log.gz').write_bytes(gzip.compress(initial.read_bytes(),mtime=0))
for name in ['prepare-node-arm-memory-control-20261008.py','record-node-arm-memory-20261008.py']:
    shutil.copy2(root/'work'/name,out/name)
review=[]
for path,needles in [
    ('deps/v8/src/compiler/backend/arm64/instruction-selector-arm64.cc',['GetStoreOpcodeAndImmediate(', 'GetLoadOpcodeAndImmediate(']),
    ('deps/v8/src/compiler/backend/instruction-selector-adapter.h',['ts_loaded_rep()','ts_result_rep()','ts_stored_rep()']),
    ('deps/v8/src/compiler/turboshaft/operations.h',['LoadOp(OpIndex base','MemoryRepresentation stored_rep','loaded_rep.ToRegisterRepresentation()']),
    ('deps/v8/src/compiler/turboshaft/representations.h',['explicit constexpr MemoryRepresentation(Enum','constexpr MemoryRepresentation()']),
]:
    p=source/path; lines=p.read_text().splitlines()
    hits=[i for i,line in enumerate(lines) if any(needle in line for needle in needles)]
    review.append({'file':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
        'excerpts':[{'line':i+1,'text':'\n'.join(lines[max(0,i-2):i+14])} for i in hits]})
(out/'producer-review.json').write_text(json.dumps(review,indent=2)+'\n')
raw=(root/'results/node-native-rev5-live-20261008/aarch64-final.log').read_text()
diags=[]
for line in [900,1211,1269]:
    expected=f'../deps/v8/src/compiler/backend/arm64/instruction-selector-arm64.cc:{line}:1: warning: control reaches end of non-void function [-Wreturn-type]'
    assert expected in raw,expected
    diags.append(expected)
loader=importlib.util.spec_from_file_location('audit',root/'work/write-scoped-audit.py')
audit=importlib.util.module_from_spec(loader);loader.loader.exec_module(audit)
passes={
    9:'Standalone controls and recorder scripts carry 2026 copyright. Exact upstream extracts retain the V8 BSD license.',
    53:'No production source, flags, suppression or fallback changes. Three reviewed exhaustive-enum switches use the already approved compiler policy.',
    54:'Native control state uses stack values. Rejection adapters throw a trivial type and unwind before the next case. All six Valgrind executions free every allocation.',
    55:'Controls are single-threaded and modify no shared production state.',
    56:'Exact fixed-underlying-type enum declarations and selector bodies are retained. Typed adapters preserve enum values, opcode labels and tuple results; -Werror=switch-enum rejects omitted declared modes.',
    57:'451 distinct selector-input combinations are enumerated in each feature/mode configuration without redundant stress loops. Production runtime cost is unchanged.',
    58:'Unsupported stored/loaded representations, invalid paired stores, sandbox-disabled protected loads and debug register mismatches are checked as rejections. Unnamed enum values are excluded by internal producer invariants.',
    59:'Evidence states all adapter boundaries, unchecked release-mode invariants, supported feature combinations and lack of native ARM instruction execution.',
    61:'Controls use fixed command arrays and no network. No user-controlled memory or external service is modified.',
    62:'All three original warnings reproduce in all six configurations. Every named input representation is checked against independent expected opcode tables. All 5,412 case executions pass normally/under Valgrind, with zero errors and all allocations freed.',
}
audit.write(out/'audit.rst','V8 ARM memory-selector diagnostic audit',
    'Scope: three unchanged selector functions, producer review and standalone branch controls. All 62 checks: 10 Pass, 52 N/A, 0 Fail. Native ARM execution and package qualification remain open.',
    passes,'No Qore module, QPP, DataProvider, JNI or public API changes. Standalone finite controls execute outside a cancellable Qore program; production I/O, loops and blocking behavior are unchanged.')
record={
    'schema':1,'date':'2026-10-08','copyright':'Copyright 2026 Qore Technologies, s.r.o.',
    'status':'Three exhaustive-enum ARM selector diagnostics reviewed and qualified under the existing policy; native package/runtime qualification remains open.',
    'diagnostics':diags,
    'root_cause':'All declared representation values either select an opcode tuple or terminate through CHECK/UNREACHABLE. GCC also considers unnamed fixed-underlying-type enum values, which the typed internal graph producers must not supply.',
    'producer_invariants':[
        'The active load selector receives loaded_rep and result_rep directly from the typed LoadOp via LoadView; LoadOp validation checks their consistency.',
        'The active store selector receives typed StoreOp.stored_rep and explicitly paired=false. The controls also cover the helper\'s paired branches.',
        'The legacy one-argument load overload has no call in this ARM translation unit; its entire named representation/semantic cross-product is nevertheless checked.',
        'Invalid/default MemoryRepresentation sentinels are not a legal graph representation. Tests do not execute undefined fallthrough for fabricated enum values.'],
    'qualification':{'configurations':records,'cases_per_execution':451,'total_normal_and_valgrind_cases':5412,
                     'valgrind_errors':0,'all_allocations_freed':True},
    'approval':{'basis':'Existing user-approved V8 exhaustive-enum policy; no new approval is claimed.',
                'evidence':'evidence/node-gcc-return-policy-proposal-20261006.json'},
    'limits':[
        'Exact enum declarations, ImmediateMode, IsUnsigned and selector bodies are extracted unchanged. Graph/storage wrapper classes and numeric opcode values are replaced by typed adapters preserving selection identities; no ARM instructions are emitted or executed.',
        'CHECK and UNREACHABLE throw only in the control to verify rejection. Production fatal behavior is unchanged. The release DCHECK adapter uses an unevaluated sizeof comparison, preserving runtime non-evaluation while checking adapter types.',
        'The initial release adapter erased DCHECK arguments and introduced one unused-parameter warning under -Wextra. The final type-checked adapter removes that harness artifact; initial output is retained. Final compilations contain only the three reproduced policy-covered warnings.',
        'Release-mode register mismatches exercise the selector\'s unchecked output, not a supported public input contract. Debug mode independently rejects mismatches.',
        'Only supported compression/sandbox combinations (off/off, on/off, on/on) are tested.',
        'Full native x86_64/aarch64 OBS revision6 builds and installed V8 module checks remain required.'],
    'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}}
(root/'evidence/node-arm-memory-diagnostics-20261008.json').write_text(json.dumps(record,indent=2)+'\n')
print('Qualified three ARM selector warnings: 451 cases x six configurations x normal/Valgrind = 5412 checks.')
