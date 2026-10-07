# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from html.parser import HTMLParser
import json,hashlib
root=Path.cwd();out=root/'results/core-doc-literals15-20261007'
class Visible(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.parts=[]
 def handle_data(self,s):self.parts.append(s)
def text(p):
 v=Visible();v.feed(p.read_text());v.close();return ''.join(v.parts)
record={}
for target,rows in json.loads((out/'status.json').read_text()).items():
 assert len(rows)==9 and all(r['exit_code']==0 for r in rows)
 assert all(not r['diagnostics'] for r in rows if r['variant']=='fixed')
 base=out/target/'fixed';notes=base/'lang-render/html/release_notes.html';http=base/'lang-render/html/class_qore_1_1_h_t_t_p_client.html';table=base/'TableMapper/html/index.html'
 assert 'esmtptls://user:password@smtp.example.com' in text(notes)
 assert '\\n, \\r, or \\r\\n' in text(notes)
 assert '{}|\\^~[]`' in text(http)
 assert 'queueData(list,' in text(table)
 for p in [notes,http,table]:assert not any(c in text(p) for c in ['&#64;','&#92;','&#96;']),p
 record[target]={'fixed_passes':7,'original_diagnostics':sum(len(r['diagnostics']) for r in rows if r['variant']=='original'),'rendered_literal_checks':4,'pages_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [notes,http,table]}}
assert record['fedora']['original_diagnostics']==10
(root/'results/core-doc-literals15-review-20261007.json').write_text(json.dumps(record,indent=2)+'\n');print('21 clean rendering/index passes; 12 displayed-literal checks; original Fedora reproduces 10 diagnostics')
