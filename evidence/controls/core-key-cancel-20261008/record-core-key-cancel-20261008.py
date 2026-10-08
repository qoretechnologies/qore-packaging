# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip,hashlib,json,re,runpy,shutil,subprocess
root=Path('/home/david/src/qore/git/qore-packaging');repo=root.parent/'qore';base=root/'results/core-key-cancel-20261008'
assert json.loads((base/'status.json').read_text())['exit_code']==0
source=json.loads((base/'source.json').read_text())
for n,h in source['files_sha256'].items():assert hashlib.sha256((repo/n).read_bytes()).hexdigest()==h,n
results={}
for mode in ['debug','release']:
 directory=base/mode;steps=json.loads((directory/'steps.json').read_text());assert len(steps)==11 and all(s['exit_code']==0 for s in steps)
 assert (directory/'qore-hash-key-cancel-test.log').read_text()=='PASS: 172 hash key cancellation checks\n'
 assert (directory/'qore-hash-lookup-test.log').read_text()=='PASS: 348 hash lookup checks\n'
 build=(directory/'build.log').read_text();assert not re.search(r'(?im)warning:|error:',build)
 config=(directory/'configure.log').read_text();assert config.count('CMake Warning')==2
 for backend in ['quictls','libressl']:assert 'libngtcp2_crypto_'+backend+' library is disabled' in config
 for name in ['qore-hash-key-cancel-test','qore-hash-lookup-test']:
  text=(directory/(name+'-valgrind.log')).read_text();assert 'ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)' in text
  assert all(re.search(k+r' lost:\s+0 bytes in 0 blocks',text) for k in ['definitely','indirectly','possibly'])
  warnings=[line for line in text.splitlines() if 'Warning:' in line];assert len(warnings)==1 and 'zero subprog, missing DW_AT_abstract_origin' in warnings[0]
 cases=assertions=0
 for name in ['hash-key-cancel','hash-lookup-native','hash','hashdecl','hash-key-encoding']:
  text=(directory/(name+'.log')).read_text();assert not re.search(r'(?im)warning encountered|^warning:|^error:|Skipped:',text)
  counts=re.findall(r'Ran (\d+) test cases?, (\d+) succeeded \((\d+) assertions\)',text);assert len(counts)==1 and counts[0][0]==counts[0][1]
  cases+=int(counts[0][0]);assertions+=int(counts[0][2])
 assert (cases,assertions)==(19,2025)
 results[mode]={'native_cancellation_checks':172,'native_lookup_checks':348,'qore_cases':cases,'qore_assertions':assertions,'valgrind_runs':2,'memory_errors':0,'lost_bytes':0}
write=runpy.run_path(str(root/'work/write-scoped-audit.py'))['write']
passes={
9:'The helper, both new tests and this audit carry Copyright 2026.',
13:'hash-key-cancel.qtest uses %modern.',14:'The qtest is executable (0755).',
15:'The local qlib path precedes a hard relative import of ../../../../qlib/QUnit.qm.',
16:'QUnit is delivered with Qore; no external module dependency is introduced.',
17:'No production filesystem operation is added; test subprocess launch selects the native fixture explicitly.',
18:'No network operation is introduced.',20:'No File, Dir, Socket or HTTPClient operation is added to Qore code.',
21:'Runtime constructors provide their exception sink to the chunked scan. The outer loop checks cancellation each chunk and the inner loop is bounded to 100 bytes. The existing non-throwing invariant-only form remains separate from runtime constructors.',
22:'The new check uses qore_check_cancel; no deprecated cancellation API is added.',
23:'At most 100 byte inspections occur between checks. size - i bounds the chunk without addition overflow.',
24:'No production blocking operation is introduced. Native fixtures request cancellation synchronously with no sleeps or polling.',
53:'The missing cancellation point is fixed in the scanning operation itself. No production flag, warning filter, feature disablement or workaround is added.',
54:'Both constructors stop after scan cancellation and preserve an empty invalid helper. Runtime hash APIs clear existence outputs on errors. Test-owned Qore objects use ReferenceHolder/ProgramHelper; cancellation/interrupt guards clear state on exception exits.',
55:'Production state remains stack-local; existing cancellation APIs own synchronization. The fixture counter is used only by its single test thread.',
56:'Offsets and counts use size_t; byte inspection uses unsigned char; fixture objects and exception sinks remain strongly typed.',
57:'Scanning remains linear without copying or allocation. Default-encoding/inline paths retain constant-time selection; cancellation cost is amortized over 100 bytes.',
58:'Tests cover empty keys, chunk boundaries, non-ASCII bytes, initially true/false existence flags, thread cancellation, program interruption, cleanup deferral and recovery.',
59:'Internal API comments describe cancellation and the invariant-only predicate. The durable cancellation design and release notes document implemented behavior.',
61:'The chunk length never exceeds the remaining input. Tests verify input bytes survive cancellation; no credentials or new external I/O are introduced.',
62:'Both builds pass 172 new checks, 348 lookup checks and 19 Qore cases/2025 assertions, including all four execution modes and AOT. Four Valgrind runs have zero memory errors or lost allocations. The original library reproducibly completed a 1 MiB lookup with cancellation pending.'}
audit=repo/'examples/test/qore/misc/audits/hash-key-cancel.rst'
write(audit,'Hash key scan cancellation audit','Scope: QoreHashKeyHelper.h, its native/Qore regression, CMake target, cancellation design and release notes. All 62 checks reviewed: 21 Pass, 41 N/A, 0 failures. Debug and Release qualification: qore-packaging/evidence/core-key-cancel-20261008.json. Only the already-approved optional ngtcp2 backend notices and GCC/Valgrind DW_AT_abstract_origin diagnostic remain; no new diagnostic exception is requested.',passes,'No corresponding new installed Qore module, QPP class, DataProvider registration, JNI component, sandbox I/O helper or QPP flag change in this scope.')
assert len(passes)==21
out=root/'evidence/controls/core-key-cancel-20261008';out.mkdir()
for folder in ['core-key-cancel-20261008','core-key-cancel-control-20261008']:
 for path in sorted((root/'results'/folder).rglob('*')):
  if not path.is_file() or path.suffix not in ['.log','.json']:continue
  dest=out/folder/path.relative_to(root/'results'/folder);dest.parent.mkdir(parents=True,exist_ok=True)
  if path.suffix=='.log':dest.with_suffix('.log.gz').write_bytes(gzip.compress(path.read_bytes(),mtime=0))
  else:shutil.copyfile(path,dest)
for name in ['core-key-cancel-control-20261008.cpp','qualify-core-key-cancel-20261008.py','record-core-key-cancel-20261008.py']:
 shutil.copyfile(root/'work'/name,out/name)
shutil.copyfile(audit,out/audit.name)
paths=list(source['files_sha256'])+[str(audit.relative_to(repo))]
record={'schema':1,'copyright':'Copyright 2026 Qore Technologies, s.r.o.','date':'2026-10-08','status':'Qualified and fully audited; ready to commit.','base_commit':source['head'],'root_cause':'The new helper scanned an arbitrarily long non-default ASCII-compatible key without a cancellation point. A pending request was left untouched while a 1 MiB lookup returned its value.','fix':'Scan at most 100 bytes between qore_check_cancel calls and propagate failure before attempting conversion. Default-encoding and inline fast paths are unchanged.','qualification':results,'audit':{'pass':21,'na':41,'fail':0},'approved_diagnostics':['evidence/ngtcp2-backend-diagnostics-20261008.json','Previously approved exact GCC/Valgrind missing-DW_AT_abstract_origin diagnostic.'],'limits':['Cancellation/interruption is injected deterministically before lookup; tests do not race a cancellation request with a timed scan. Source structure bounds subsequent check intervals to 100 bytes.','Updated RPM qualification and native repository checks remain separate gates.'],'source_sha256':{n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in paths},'files_sha256':{str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(out.rglob('*')) if path.is_file()}}
(root/'evidence/core-key-cancel-20261008.json').write_text(json.dumps(record,indent=2)+'\n')
print('PASS: both build modes, four clean memory runs and all 62 audit entries; seven source paths pinned')
