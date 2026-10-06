# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,re,subprocess
root=Path('results/fedora-geos-metadata-candidate3-20261006/rpmbuild/BUILD');binary,=[p for p in root.rglob('geos-api-2.0.qmod') if 'BUILDROOT' not in p.parts]
s=subprocess.check_output(['readelf','--debug-dump=info',str(binary)],text=True,stderr=subprocess.PIPE);dies=[];current=None
for line in s.splitlines():
 m=re.match(r'\s*<(\d+)><([0-9a-f]+)>: Abbrev Number: \d+ \((DW_TAG_\w+)\)',line)
 if m:
  current={'depth':int(m[1]),'offset':m[2],'tag':m[3],'attributes':[]};dies.append(current)
 elif current and 'DW_AT_' in line:current['attributes'].append(line.strip())
by_offset={d['offset']:d for d in dies}
stack={};records=[]
for die in dies:
 depth=die['depth'];stack={k:v for k,v in stack.items() if k<depth}
 if die['tag']=='DW_TAG_inlined_subroutine' and not any('DW_AT_abstract_origin' in l for l in die['attributes']):
  records.append({'die':die,'parents':[v for k,v in sorted(stack.items()) if v['tag'] in ('DW_TAG_subprogram','DW_TAG_inlined_subroutine')]})
 stack[depth]=die
for record in records:
 names=[]
 for parent in record['parents']:
  item=parent;seen=set()
  while item['offset'] not in seen:
   seen.add(item['offset']);names.extend(a for a in item['attributes'] if 'DW_AT_name ' in a or 'DW_AT_linkage_name' in a)
   refs=[re.search(r'<0x([0-9a-f]+)>',a)[1] for a in item['attributes'] if 'DW_AT_abstract_origin' in a or 'DW_AT_specification' in a]
   if not refs or refs[0] not in by_offset:break
   item=by_offset[refs[0]]
 record['resolved_parent_names']=names
pcs=[]
for r in records:
 attrs=r['die']['attributes'];low=[int(a.split(':')[-1],16) for a in attrs if 'DW_AT_low_pc' in a];high=[int(a.split(':')[-1],16) for a in attrs if 'DW_AT_high_pc' in a]
 if low and high and high[0]>0:pcs.append((low[0],high[0],r))
for low,size,r in pcs[:6]:
 r['code_context']=subprocess.check_output(['objdump','-d','-C','--start-address='+hex(low-16),'--stop-address='+hex(low+size+8),str(binary)],text=True)
out=Path('results/geos-tls-dwarf-20261006.json');out.write_text(json.dumps({'binary':str(binary),'sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'missing_origin_inline_dies':records},indent=2)+'\n');print('missing-origin inline DIEs',len(records));print(json.dumps(records[:3],indent=2)[:4500])
