# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import collections, hashlib, json, re, runpy

root=Path.cwd()
source=root/'results/leap-nodejs24-obs-flags-candidate9-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
runpy.run_path('work/reconcile-node-candidate9-warnings-20261007.py')
rows=json.loads(Path('work/node-candidate9-warning-reconciliation-20261007.json').read_text())
proof=[]
for name in ('node-guarded-state-diagnostics-20261006','node-memory2-diagnostics-20261006',
             'node-cc-load-diagnostic-20261007','node-snapshot-copy-diagnostic-20261007'):
    evidence=json.loads(Path('evidence/'+name+'.json').read_text())
    for file,digest in evidence['source_sha256'].items():
        relative=file if file.startswith('deps/') else 'deps/v8/'+file
        actual=hashlib.sha256((source/relative).read_bytes()).hexdigest()
        assert actual==digest,(relative,actual,digest)
        proof.append(dict(file=relative,sha256=actual,evidence=name))
gc=json.loads(Path('evidence/controls/node-gc-transition-20261006/source-extracts.json').read_text())
intl=next(row for row in gc if row['file']=='deps/v8/src/objects/intl-objects.cc')
assert intl['body'] in (source/intl['file']).read_text()
proof.append(dict(file=intl['file'],body_sha256=intl['sha256'],evidence='node-gc-transition-diagnostics-20261006'))
class_sites=json.loads(Path('evidence/node-class-memory-diagnostics-20261006.json').read_text())['partial_build_sites']
def ascii_quotes(text):return text.replace('‘',"'").replace('’',"'")
for row in rows:
    if row['status']=='approved source family; final context comparison required':
        evidence=row['evidence'][0]
        if evidence=='node-class-memory-diagnostics-20261006.json':
            diagnostic=ascii_quotes(row['diagnostic'].split('warning: ',1)[1].rsplit(' [-W',1)[0])
            matched=any(site['file']==row['file'] and site['line']==row['line'] and
                        site['diagnostic']==diagnostic for site in class_sites)
            if not matched:
                assert 'SnapshotTable<v8::internal::maglev::ValueNode*>::LogEntry' in diagnostic
                row['status']='new exact SnapshotTable instantiation; focused qualification pending'
                row['evidence']=[]
                continue
        elif row['file']=='/usr/include/c++/13/ostream':
            row['status']='new exact Torque C++ load site; focused qualification pending'
            row['evidence']=[]
            continue
        else:
            assert evidence in ('node-guarded-state-diagnostics-20261006.json',
                'node-memory2-diagnostics-20261006.json','node-gc-transition-diagnostics-20261006.json'),row
        row['status']='approved family with final source/diagnostic identity verified'
    elif row['family']=='-Walloc-size-larger-than=':
        row['status']='Wasm metadata fix prepared in candidate 10; full LTO verification pending'
        row['evidence']=['node-wasm-deopt-fix-20261007.json']
extracts=json.loads(Path('work/node-candidate9-return-extracts-20261007.json').read_text())
for row in extracts:
    data=(source/row['file']).read_bytes()
    assert hashlib.sha256(data).hexdigest()==row['source_sha256']
    assert row['body'] in data.decode()
    assert hashlib.sha256(row['body'].encode()).hexdigest()==row['body_sha256']
Path('work/node-candidate9-warning-context-verified-20261007.json').write_text(json.dumps({
    'source_identity':proof,'additional_return_endings':extracts,'diagnostics':rows,
    'limits':'Return-path source review is scoped to declared enum values and documented object invariants. Corrupted enum storage is not certified. The two newly isolated sites have exact user approvals and verified source hashes. The Wasm allocation site still requires the candidate10 full LTO result.'},indent=2)+'\n')
print('Verified statuses:',dict(collections.Counter(row['status'] for row in rows)))
