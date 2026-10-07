# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import re,json,hashlib
root=Path.cwd();repo=root/'work/checkouts/qore-documentation-sdk-20261006'
token=re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|\#[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_][A-Za-z_0-9]*|[0-9]+|[^\s]')
def tokens(s):return [m[0] for m in token.finditer(s) if not m[0].startswith(('//','/*','#'))]
first={}
for directory in ['core-doc-reference-fixes-20261007','core-doc-markup-fixes-20261007','core-doc-additional-reference-fixes-20261007','core-doc-additional-markup-fixes-20261007','core-doc-render5-fixes-20261007','core-doc-literal-fixes-20261007']:
 base=root/'work'/directory/'before'
 for p in base.rglob('*'):
  if p.is_file() and p.suffix in ('.qm','.qc','.h','.qpp'):first.setdefault(str(p.relative_to(base)),p)
rows=[]
for rel,p in sorted(first.items()):
 a=p.read_bytes();b=(repo/rel).read_bytes();rows.append({'file':rel,'before':hashlib.sha256(a).hexdigest(),'after':hashlib.sha256(b).hexdigest(),'executable_tokens_equal':tokens(a.decode())==tokens(b.decode())})
report={'files':rows,'executable_changes':[r['file'] for r in rows if not r['executable_tokens_equal']]}
(root/'results/core-doc-corrections-token-review3-20261007.json').write_text(json.dumps(report,indent=2)+'\n')
print('Reviewed',len(rows),'Qore source files; executable changes:',report['executable_changes']);assert report['executable_changes'] == ['qlib/Qdx.qm']
