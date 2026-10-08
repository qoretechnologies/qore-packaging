# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil

root=Path.cwd()
source=root/'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
out=root/'evidence/controls/node-arm-inlining-equivalence-20261008'
out.mkdir()
raw_path=root/'results/node-native-rev5-live-20261008/aarch64-final.log'
raw=raw_path.read_text().splitlines()
pending=json.loads((root/'results/node-arm-diagnostics-remaining-20261008.json').read_text())
rows=[
    ('optional_link_begin','ast/ast-source-ranges.h:322:9',
     'parsing/parser-base.h:3921:7','node-optional-link-diagnostic-20261007',
     'node-optional-link-20261007','bool optional_chaining = false;',
     'ParseLeftHandSideContinuation assigns the source position before is_optional becomes true. The ARM diagnostic follows that same value through SourceRange and RecordExpressionSourceRange into ExpressionSourceRanges.'),
    ('untagged','maglev/maglev-ir.h:1342:37',
     'maglev/maglev-phi-representation-selector.cc:632:18','node-phi-diagnostics-20261007',
     'node-phi-20261007','ValueNode* untagged;',
     'The same ConvertTaggedPhiTo local is assigned by each supported representation or the branch terminates. ARM reports the Input constructor reached through the already-reviewed phi change_input, rather than add_use.'),
    ('result','maglev/maglev-ir.h:5924:11',
     'maglev/maglev-ir.h:5813:20','node-object-dispatch-diagnostics-20261007',
     'node-object-dispatch-20261007','VirtualObject* Clone(',
     'The unchanged VirtualObject::Clone assigns its result for kDefault and terminates for the other declared types. The previously reviewed MergeVirtualObject caller forwards that returned value to VirtualObjectList::Add; the ARM warning names this later store.'),
    ('replacement','objects/js-date-time-format.cc:1830:22',
     'objects/js-date-time-format.cc:1792:12','node-hourcycle-diagnostics-20261006',
     'node-hourcycle-20261006','ReplaceHourCycleInPattern(',
     'The same ReplaceHourCycleInPattern local is assigned for every concrete HourCycle, while kUndefined returns first. ARM reports the append use after inlining into the cache path instead of the declaration.'),
    ('scope_id','tracing/trace-event.h:217:54',
     'heap/heap.cc:1948:30','node-sweep-serializer-diagnostics-20261007',
     'node-sweep-serializer-20261007','void CompleteArrayBufferSweeping(',
     'Both diagnostics arise from CompleteArrayBufferSweeping, which assigns scope_id for all three GarbageCollector values. The ARM warning names AddTraceEvent in the same macro expansion, one line after the prior TraceID constructor.'),
]
records=[]
for variable,site,declaration,evidence,folder,needle,explanation in rows:
    matching=[r for r in pending if site in r['diagnostic']]
    assert len(matching)==1,(site,matching)
    diagnostic=matching[0]['diagnostic']
    assert f'‘{variable}’ may be used uninitialized [-Wmaybe-uninitialized]' in diagnostic
    ref_path=root/'evidence'/(evidence+'.json')
    ref=json.loads(ref_path.read_text())
    assert ref.get('approval','').startswith('Allow ')
    for rel,sha in ref['files_sha256'].items():
        assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==sha,rel
    extracts=json.loads((root/'evidence/controls'/folder/'source-extracts.json').read_text())
    if isinstance(extracts,dict):
        extracts=list(extracts['bodies'].values())
    verified=[]
    for extract in extracts:
        body=extract['body'];file=extract.get('file',extract.get('path'))
        assert body in (source/file).read_text(),file
        assert hashlib.sha256(body.encode()).hexdigest()==extract['sha256']
        if needle in body:
            verified.append({'file':file,'line':extract['line'],'sha256':extract['sha256'],'body':body})
    assert len(verified)==1,(site,verified)
    indexes=[i for i,line in enumerate(raw) if diagnostic in line]
    assert indexes
    blocks=[]
    for i in indexes:
        end=next(j for j in range(i,min(i+50,len(raw))) if declaration in raw[j] and 'note:' in raw[j])+3
        block='\n'.join(line for line in raw[max(0,i-7):end] if 'g++ -o' not in line)
        assert f'‘{variable}’ was declared here' in block
        blocks.append(block)
    record={'diagnostic':diagnostic,'declaration':declaration,'variable':variable,
            'existing_approval':'evidence/'+evidence+'.json','existing_approval_sha256':hashlib.sha256(ref_path.read_bytes()).hexdigest(),
            'existing_evidence_files_verified':len(ref['files_sha256']),
            'same_dataflow':explanation,'source_identity':verified,'arm_compiler_call_chains':blocks}
    records.append(record)
(out/'equivalence.json').write_text(json.dumps(records,indent=2)+'\n')
shutil.copy2(Path(__file__),out/'record.py')
loader=importlib.util.spec_from_file_location('audit',root/'work/write-scoped-audit.py')
audit=importlib.util.module_from_spec(loader);loader.loader.exec_module(audit)
audit.write(out/'audit.rst','Node ARM inlining diagnostic identity audit',
    'Scope: five compiler-location mappings to already approved, unchanged data flows. All 62 checks: 9 Pass, 53 N/A, 0 Fail. No acceptance is extended to another variable, function, representation or runtime behavior.',
    {9:'The recorder and evidence carry 2026 copyright.',
     53:'No source patch, compiler-flag change, suppression or diagnostic exception is introduced. Mapping follows exact variable declarations and compiler inlining notes, not message similarity.',
     54:'Read-only verification fails on missing files, mismatched source, checksums, declarations or approval records. No C++ ownership behavior changes.',
     55:'Verification is sequential and does not modify active build trees. Existing validated controls and native architecture gates remain unchanged.',
     56:'Each warning is tied to one exact declaration, unchanged complete branch/function extraction and the corresponding approved evidence record.',
     58:'Assertions reject missing/ambiguous matches and differing source bodies. All referenced evidence file digests are verified before reconciliation.',
     59:'The record states the declaration-to-inlined-use mapping, exact source identity, original approval and retained qualification limits.',
     61:'No network, shell interpolation, runtime mutation or user-controlled program input is introduced by the verifier.',
     62:'All five compiler call chains identify the already qualified locals. Complete relevant source fragments and all five existing evidence manifests verify byte for byte. Existing native/JavaScript/Valgrind results remain applicable to those unchanged functions; no new ARM execution is claimed.'},
    'No new runtime code, Qore modules, QPP classes, DataProvider features, JNI assets, public APIs or Qore tests. This is read-only evidence reconciliation.')
record={'schema':1,'date':'2026-10-08','copyright':'Copyright 2026 Qore Technologies, s.r.o.',
    'status':'Five additional ARM warning locations resolve to existing approved data flows after exact source/declaration/call-chain verification.',
    'source_log_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    'mappings':[{k:v for k,v in r.items() if k not in ['source_identity','arm_compiler_call_chains']} for r in records],
    'approval_basis':'Existing approvals cover these same qualified locals/functions. No additional behavior or diagnostic family is accepted; only compiler inlining locations differ.',
    'limits':['All original control limits and source assumptions remain. This evidence does not claim new native ARM execution.',
              'The five prior native/JavaScript/Valgrind qualification records are reused because their exact production source bodies are unchanged; no duplicate test run is claimed.',
              'Other ARM warnings remain unresolved and are excluded from these mappings.'],
    'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}}
(root/'evidence/node-arm-inlining-equivalence-20261008.json').write_text(json.dumps(record,indent=2)+'\n')
print('Verified five exact declaration/source/call-chain equivalences against existing approved evidence.')
