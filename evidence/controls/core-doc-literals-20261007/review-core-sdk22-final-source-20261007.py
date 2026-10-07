# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,re,subprocess,hashlib
root=Path.cwd();repo=root/'work/checkouts/qore-documentation-sdk-20261006'
changed=subprocess.check_output(['git','-C',str(repo),'diff','--name-only','HEAD','-z']).decode().split('\0')
token=re.compile(r'//[^\n]*|/\*[\s\S]*?\*/|\#[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[A-Za-z_][A-Za-z_0-9]*|[0-9]+|[^\s]')
def tokens(s):return [m[0] for m in token.finditer(s) if not m[0].startswith(('//','/*','#'))]
rows=[]
for rel in filter(None,changed):
 if Path(rel).suffix not in ['.h','.cpp','.qpp','.qm','.qc']:continue
 a=subprocess.check_output(['git','-C',str(repo),'show','HEAD:'+rel]);b=(repo/rel).read_bytes()
 rows.append({'file':rel,'old_sha256':hashlib.sha256(a).hexdigest(),'new_sha256':hashlib.sha256(b).hexdigest(),'tokens_equal':tokens(a.decode())==tokens(b.decode())})
unequal=[x['file'] for x in rows if not x['tokens_equal']]
expected={'qlib/Util.qm','qlib/Qdx.qm','modules/yaml/src/QC_YamlDocumentIterator.qpp','modules/yaml/src/QC_YamlSaxParser.qpp','modules/yaml/src/QC_YamlStreamWriter.qpp','modules/yaml/src/ql_yaml.qpp'}
assert set(unequal)==expected,unequal
original=subprocess.check_output(['git','-C',str(repo),'show','HEAD:qlib/Util.qm']).decode()
assert original.replace('`str += chr(b)` accumulator','<tt>str += chr(b)</tt> accumulator').replace('ESC `[` … `m`','ESC <tt>[</tt> … <tt>m</tt>')==(repo/'qlib/Util.qm').read_text()

for rel in ['qlib/Qdx.qm','examples/test/qlib/Qdx/AstProcessor.qtest','rpm/tests/test_flex_source_paths.py']:
 a=(root.parent/'qore'/rel).read_text();b=(repo/rel).read_text()
 if rel=='qlib/Qdx.qm':a=a.replace('    - initial release\n','    - the initial version of the Qdx module\n')
 assert a==b,rel
assert (repo/'qlib/WaveRestClient.qm').stat().st_mode&0o777==0o644
x={'source_files':rows,'non_comment_token_differences':unequal,'review':'The Qdx fix is identical to audited develop commit 73c284618 except one historical release-note wording correction. The four QPP lexical differences are comment-parser artifacts; actual generated C++ identity is recorded in core-doc-yaml-qpp-comparison-20261007.json. Util differs only in two verified documentation substitutions; the lightweight lexical check does not parse all Qore regex literals. No C++ implementation changes.','wave_module_mode':'0644; only source .qm previously marked executable, no interpreter entry point'}
(root/'results/core-sdk22-final-source-review-20261007.json').write_text(json.dumps(x,indent=2)+'\n');print(len(rows),'source files reviewed;',len(unequal),'already-qualified differences')
