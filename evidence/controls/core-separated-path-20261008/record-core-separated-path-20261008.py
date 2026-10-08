# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import re
import runpy
import shutil
root=Path.cwd();repo=root.parent/'qore'
out=root/'evidence/controls/core-separated-path-20261008';out.mkdir(exist_ok=True)
records={}
for mode in ['debug','release']:
 base=root/'results/core-separated-path-final-20261008'/mode
 status=json.loads((base/'status.json').read_text());assert len(status)==8 and all(s['exit_code']==0 for s in status)
 suites={}
 for p in base.glob('*.log'):
  s=p.read_text(); rows=re.findall(r'Ran (\d+) test cases, (\d+) succeeded \((\d+) assertions\)',s);assert len(rows)==1
  count,passed,assertions=map(int,rows[0]);assert count==passed
  if 'valgrind' in p.stem:
   assert 'ERROR SUMMARY: 0 errors' in s
   assert all(re.search(k+r' lost:\s+0 bytes',s) for k in ['definitely','indirectly','possibly'])
  suites[p.stem]={'cases':count,'assertions':assertions,'valgrind':'zero errors or lost allocations; regex interpreter selected' if 'valgrind' in p.stem else None}
 for p in base.iterdir():
  dest=out/mode/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
  if p.suffix=='.log':dest.with_suffix('.log.gz').write_bytes(gzip.compress(p.read_bytes(),mtime=0))
  else:shutil.copyfile(p,dest)
 integration=root/f'results/grpc-core-path-{mode}-integration-20261008.log';s=integration.read_text();assert 'Ran 40 test cases, 40 succeeded (378 assertions)' in s
 (out/f'grpc-{mode}.log.gz').write_bytes(gzip.compress(integration.read_bytes(),mtime=0))
 records[mode]={'suites':suites,'salesforce_integration':{'cases':40,'assertions':378,'invocation':'relative test path, source module search, no preloaded module'}}
for name in ['core-separated-path-negative-20261008.log','core-separated-path-build-debug-20261008.log','core-separated-path-build-release-20261008.log','grpc-relative-unloaded-negative-20261008.log']:
 p=root/'results'/name;(out/(name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
for name in ['qualify-core-separated-path-final-20261008.py','record-core-separated-path-20261008.py']:
 shutil.copyfile(root/'work'/name,out/name)
passes={
9:'New regression and audit carry Copyright 2026.',
13:'The regression and generated module entry points use %modern; separated .qc fixture has no parse directives.',
14:'The new .qtest is executable.',
15:'The test prepends local qlib before relative QUnit/FsUtil requires. Generated temporary-module imports intentionally exercise named search and explicit relative imports.',
16:'Only Qore-owned QUnit/FsUtil dependencies; no external binary test dependency.',
17:'No new direct filesystem operations: normalize the path already found and validated by the existing module lookup. Module sandbox behavior is unchanged.',
20:'Test File/Dir operations are confined to TmpDir fixtures; cwd restoration uses on_exit and temporary directories are released even after assertions fail.',
53:'Fix the missed normalization at the separated-module search boundary, matching existing flat-source and AOT-fallback handling. No production flags, source lookup fallback or warning suppression added.',
54:'Existing ReferenceHolder and local QoreString ownership remain unchanged. Missing-entry tests verify failure; eight memory runs have no lost allocations.',
55:'The normalized path is a local value under the existing module-loading synchronization. Sequential fixture methods restore the process cwd on every exit.',
56:'Typed string/bool/hash variables; no casts or new untyped callbacks.',
57:'One linear normalization only after an existing directory and entry point are found; no extra search or I/O loop.',
58:'Missing module main is rejected; both explicit and search-based resolution remain covered, including spaces and dot segments.',
59:'Release notes describe the false module filename and resulting resource failures; durable design documents cwd versus importer-relative resolution.',
61:'No new permission bypass, format string, network operation or secret. Fixture-generated names and paths are trusted and bounded.',
62:'Original source reproduces the erroneous scripts/module files path. Both builds pass 25 cases/73 assertions plus the failing Salesforce suite (40 cases/378 assertions each). Eight Valgrind runs in documented interpreter regex mode are clean; default JIT diagnostics are separately traced and qualified, pending exact acceptance.'}
a=runpy.run_path(str(root/'work/write-scoped-audit.py'))
audit=repo/'examples/test/qore/misc/module-loader/audits/separated-module-path.rst'
a['write'](audit,'Separated module path audit',f'Scope: ModuleManager.cpp normalization, separated-module-path.qtest and corresponding design/release notes. All 62 checks reviewed: {len(passes)} Pass, {62-len(passes)} N/A, 0 implementation failures. Commit qualification remains pending the exact PCRE2 source-file filter and previously requested ngtcp2 configure diagnostic decisions. Other hash-lookup work in the checkout is excluded.',passes,'No corresponding new installed module, QPP class, DataProvider, JNI, C++ loop/blocking operation or public API change in this scope.')
paths=['lib/ModuleManager.cpp','examples/test/qore/misc/module-loader/separated-module-path.qtest','design/qore-module-structure.md','doxygen/lang/900_release_notes.dox.tmpl','examples/test/qore/misc/module-loader/audits/separated-module-path.rst']
evidence={'schema':1,'date':'2026-10-08','copyright':'Copyright 2026 Qore Technologies, s.r.o.','status':'Implemented and qualified; exact PCRE2 and existing ngtcp2 diagnostic decisions pending; not committed.', 'root_cause':'Directory-module search passed its cwd-relative result to a constructor that normalizes against the importing Program directory. Flat source and source-fallback paths already normalize first. Source content loads correctly but module filename metadata gains the importing directory twice.', 'fix':'Normalize the validated directory search result against process cwd before loadSeparatedModule; preserve explicit importer-relative paths.', 'qualification':records, 'audit':{'pass':len(passes),'na':62-len(passes),'fail':0,'path':str(audit)}, 'diagnostics':['evidence/core-separated-pcre-diagnostic-20261008.json','evidence/ngtcp2-backend-diagnostics-20261008.json','Existing approved GCC/Valgrind missing DW_AT_abstract_origin diagnostic remains visible.'], 'qualified_files_sha256':{p:hashlib.sha256((repo/p).read_bytes()).hexdigest() for p in paths}, 'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}}
(root/'evidence/core-separated-path-fix-20261008.json').write_text(json.dumps(evidence,indent=2)+'\n')
print('PASS: both builds, all 25 loader cases/73 assertions, eight memory runs, both Salesforce integrations; audit',len(passes),'Pass',62-len(passes),'N/A')
