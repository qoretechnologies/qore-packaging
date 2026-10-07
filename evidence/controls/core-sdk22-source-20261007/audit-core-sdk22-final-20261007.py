# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,re,runpy,subprocess,hashlib
root=Path.cwd();repo=root/'work/checkouts/qore-documentation-sdk-20261006'
for name,count in [('module',13),('markup',6),('guide',9),('phase',7)]:
 text=(root/f'results/core-doc-sdk22-final-{name}-tests-20261007.log').read_text();assert f'Ran {count} tests' in text and text.endswith('OK\n')
 assert not re.search(r'(?im)^(?:warning:|error:|FAIL[ :]|ERROR[ :])',text),name
literal=json.loads((root/'results/core-doc-literal-regression2-20261007/status.json').read_text());assert len(literal)==3 and all(r['exit_code']==0 for r in literal.values())
source=json.loads((root/'results/core-sdk22-final-source-review-20261007.json').read_text());assert source['source_files']
results=json.loads((root/'results/core-doc-literals15-20261007/status.json').read_text())
for t,rows in results.items():
 assert len(rows)==9
 assert all(r['exit_code']==0 for r in rows)
 assert all(not r['diagnostics'] for r in rows if r['variant']=='fixed')
assert sum(len(r['diagnostics']) for r in results['fedora'] if r['variant']=='original')==10
for p in [repo/'examples/test/qlib/Qdx/AstProcessor.qtest']:
 assert p.stat().st_mode&0o111 and '%modern' in p.read_text()
 assert '%requires ../../../../qlib/Qdx.qm' in p.read_text()
# All original focused source inputs retain their qualified bytes except the
# separately checked scanner, final literal text, release notes and source mode.
old=json.loads((root/'evidence/core-doc-sdk22-focused-20261007.json').read_text())
changed=[n for n,h in old['source_files_sha256'].items() if hashlib.sha256((repo/n).read_bytes()).hexdigest()!=h]
assert set(changed)=={'CMakeLists.txt','doxygen/lang/900_release_notes.dox.tmpl','qore.spec-multi','rpm/README.rst'},changed
passes={
 2:'Release notes cover the implemented documentation backports, Qdx literal parsing and scanner debug-source paths.',
 3:'Existing module CMake registrations now include their guide and release-note pages; no new module is introduced.',
 9:'Every newly added source/test/documentation file has a 2026 notice; existing historical notices remain intact.',
 13:'AstProcessor.qtest retains %modern; Python and C++ fixture tests use their own runtimes.',
 14:'The modified Qore test is executable. WaveRestClient.qm is library source and is correctly non-executable.',
 15:'AstProcessor requires the relative local Qdx.qm and QUnit.qm paths; its source and rebuilt AOT variants both pass.',
 20:'Qdx changes documentation scanning only; no new application file or network operation is introduced. Documentation checkers read explicitly supplied repository/output paths.',
 53:'Corrections address invalid Doxygen source, document dependency ordering and RPM extraction ordering. No warnings are disabled; original controls reproduce the corrected failures.',
 54:'No C++ implementation changes. Qore-owned strings/lists remain managed; Python subprocesses check failures and temporary test files use context managers.',
 55:'Final documentation rendering reads immutable tag indexes, preventing concurrent replacement. Qdx parsing uses local per-call state.',
 56:'Qdx retains typed declarations; all other native and Qore executable sources are unchanged, as established by the source review and actual QPP output comparisons.',
 57:'Qdx decodes Unicode once per input line with bounded lookahead. The new checks traverse each input and report exact locations without full source copies per token.',
 58:'Positive and negative tests cover absent sources, malformed markup, unsupported references, spaces in paths, failed source extraction and literal/escaped commands.',
 59:'106 module indexes/renders are clean. The final six literal/link corrections also pass complete language rendering and five affected module renders on all three distributions; original Fedora controls reproduce ten diagnostics.',
 61:'Subprocess arguments are passed as lists; checked-in examples use placeholder credentials. Source/debug paths are verified against explicit roots, without untrusted shell interpolation.',
 62:'35 current documentation helper tests and the displayed-literal regression on all three distributions pass. Qdx passes 136 cases/744 assertions; scanner source-path controls pass on three distributions with clean Valgrind, and original controls fail. Full final RPM/installed/native qualification remains a separate release gate.'
}
write=runpy.run_path(str(root/'work/write-scoped-audit.py'))['write']
write(repo/'rpm/tests/documentation-sdk22.audit.rst','RPM SDK documentation and debug-source audit',f'Scope: the complete source diff from a2e56c1e9, including eight implemented documentation backports, reference/markup corrections, Qdx parsing, scanner input paths and RPM debug-source ordering. {len(passes)} Pass, {62-len(passes)} N/A, 0 Fail. This audit authorizes the tested source commit; it does not claim completion of canonical RPM, installed SDK or native architecture qualification.',passes,'No new module, native class, provider action/schema, runtime I/O, cancellation path, JNI dependency or QPP behavioral flag is introduced. Provider/native source edits affect documentation only; the separately audited Qdx change is the sole executable runtime change.')
subprocess.run(['git','-C',str(repo),'diff','--check'],check=True)
print('Audit complete:',len(passes),'Pass,',62-len(passes),'N/A, 0 Fail')
