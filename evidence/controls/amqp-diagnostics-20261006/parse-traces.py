# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,re
root=Path.cwd();out=root/'work/amqp-pcre-trace-20261006';records=[];inventories={}
for p in [root/'results/amqp-pcre-trace-20261006/run.log',*[p for t,m in [('fedora','trace'),('leap','trace2'),('el10','trace2')] for p in sorted((root/f'results/{t}-amqp-broker-{m}-20261006').glob('*.log'))]]:
 s=p.read_bytes();compiled={};pending=None;bad=set();counts={};local=[]
 # PCRE subjects can contain newlines; consume exactly the recorded byte length.
 pattern=rb'(?m)^PCRE-COMPILE (\S+) options=(\d+) pattern=(.*)$|^PCRE-MATCH (\S+) len=(\d+) start=(\d+) options=(\d+) subject=|^PCRE-RESULT (\S+) result=(-?\d+)$|^==\d+== (Conditional jump[^\n]*|Use of uninitialised[^\n]*|Invalid[^\n]*)$'
 for m in re.finditer(pattern,s):
  if m[1]:compiled[m[1]]=(int(m[2]),m[3].decode())
  elif m[4]:
   co,pat=compiled[m[4]];subject=s[m.end():m.end()+int(m[5])].decode();pending=dict(pattern=pat,compile_options=co,subject=subject,length=int(m[5]),offset=int(m[6]),options=int(m[7]))
  elif m[8]:
   assert pending is not None
   pending['result']=int(m[9]);local.append(pending);pending=None
  elif m[10]:
   assert pending is not None,(p,m[10]);pat=pending['pattern'];bad.add(pat);counts[pat]=counts.get(pat,0)+1
   assert m[10].startswith(b'Conditional jump'),m[10]
 records.extend(r for r in local if r['pattern'] in bad);inventories[str(p.relative_to(root))]=counts
records=list({json.dumps(r,sort_keys=True):r for r in records}.values());assert all(len(r['subject'].encode())==r['length'] for r in records)
(out/'all-cases.json').write_text(json.dumps(records,indent=2)+'\n');(out/'inventory.json').write_text(json.dumps(inventories,indent=2)+'\n');print(len(records),sorted({r['pattern'] for r in records}));print(json.dumps(inventories,indent=2))
