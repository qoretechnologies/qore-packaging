# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import collections,json,re
root=Path.cwd();log=root/'results/leap-nodejs24-obs-flags-candidate9-20261007/build.log';lines=log.read_text(errors='replace').splitlines()
rx=re.compile(r'^(?:\.\./)?(.+?):(\d+):\d+: warning:.*?\[(-W[^]]+)\]$')
rows=collections.Counter(line for line in lines if rx.match(line));approved={}
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for v in x.values():yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
for p in (root/'evidence').glob('node-*.json'):
 d=json.loads(p.read_text())
 if not d.get('approval'):continue
 for text in strings(d):
  for line in text.splitlines():
   if rx.match(line):approved.setdefault(line,[]).append(p.name)
register=json.loads((root/'work/node-warning-site-register-20261007.json').read_text())
return_review=json.loads((root/'evidence/node-gcc-return-policy-proposal-20261006.json').read_text())['diagnostic3_end_path_review']['sites']
return_keys={(x['file'],x['line']) for x in return_review}
return_extra=json.loads((root/'work/node-candidate9-return-extracts-20261007.json').read_text());return_keys|={(x['file'],x['line']) for x in return_extra}
extra={
 ('deps/v8/src/base/hashing.h',250):'node-maglev-inputs-diagnostic-20261006.json',
 ('deps/v8/src/compiler/node-origin-table.h',104):'node-guarded-state-diagnostics-20261006.json',
 ('deps/v8/src/tracing/trace-event.h',570):'node-guarded-state-diagnostics-20261006.json',
 ('deps/v8/src/compiler/turboshaft/assembler.h',1512):'node-graph-state-diagnostics-20261006.json',
 ('deps/v8/src/compiler/turboshaft/index.h',875):'node-graph-state-diagnostics-20261006.json',
 ('deps/v8/src/compiler/turboshaft/value-numbering-reducer.h',213):'node-graph-state-diagnostics-20261006.json',
 ('deps/v8/src/objects/intl-objects.cc',3164):'node-gc-transition-diagnostics-20261006.json',
 ('deps/v8/src/api/api.cc',224):'node-class-memory-diagnostics-20261006.json',
 ('deps/v8/src/zone/zone-containers.h',436):'node-class-memory-diagnostics-20261006.json',
 ('deps/v8/src/objects/bigint.cc',286):'node-memory2-diagnostics-20261006.json',
 ('deps/v8/src/wasm/wasm-serialization.cc',1055):'node-memory2-diagnostics-20261006.json',
 ('/usr/include/c++/13/ostream',667):'node-allocator-field-enum-diagnostics-20261006.json',
}
records=[]
for line,count in sorted(rows.items()):
 m=rx.match(line);key=(m[1],int(m[2]));family=m[3];evidence=approved.get(line,[]);status='approved exact diagnostic' if evidence else 'unclassified'
 if family=='-Wreturn-type' and key in return_keys:
  evidence=['node-gcc-return-policy-proposal-20261006.json'];status='reviewed under approved exhaustive-enum policy'
 if not evidence:
  for item in register:
   if key==(item['file'],item['line']):
    evidence=item.get('evidence',[]);status=item['status'];break
 if not evidence and key in extra:
  evidence=[extra[key]];status='approved source family; final context comparison required'
 records.append({'diagnostic':line,'occurrences':count,'file':key[0],'line':key[1],'family':family,'status':status,'evidence':evidence})
(root/'work/node-candidate9-warning-reconciliation-20261007.json').write_text(json.dumps(records,indent=2)+'\n')
print('Status counts:',dict(collections.Counter(x['status'] for x in records)))
for r in records:
 if r['status']=='unclassified' or not r['evidence']:print(r['diagnostic'])
