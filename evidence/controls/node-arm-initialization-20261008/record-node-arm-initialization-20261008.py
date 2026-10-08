# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip,hashlib,importlib.util,json,re,shutil
root=Path.cwd();out=root/'evidence/controls/node-arm-initialization-20261008';out.mkdir(exist_ok=True)
run=root/'work/node-arm-initialization-20261008';objects=root/'work/node-arm-initialization-objects-20261008';package=root/'results/node-arm-initialization-package-control-20261008';prep=root/'results/node-arm-initialization-source-20261008'
rows=json.loads((run/'status.json').read_text());assert len(rows)==18 and all(r['exit_code']==r['expected_exit'] for r in rows)
for mode in ['optimized','debug-optimized']:
 for kind in ['constructor','use']:
  prefix='fixed-'+mode+'-'+kind;normal=(run/(prefix+'-normal.log')).read_text();assert normal==('PASS: 459 constructor/copy field checks\n' if kind=='constructor' else 'PASS: 3390 actual ARM64 Operand copy/use checks\n')
  assert not (run/(prefix+'-compile.log')).read_text()
  vg=(run/(prefix+'-valgrind.log')).read_text();assert normal in vg and 'All heap blocks were freed' in vg and 'ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)' in vg
 for kind in ['operand','mem']:
  assert f'FAIL {"Operand" if kind=="operand" else "MemOperand"} immediate inactive fields' in (run/('original-'+mode+'-constructor-'+kind+'-negative.log')).read_text()
pack=json.loads((package/'status.json').read_text());assert len(pack)==4 and [r['exit_code'] for r in pack]==[1,0,0,0]
assert (package/'fixed.log').read_text()=='PASS: 4491 actual ARM64 Operand checks\nPASS: 459 constructor/copy field checks\n'
for p in package.glob('*-valgrind.log'):
 text=p.read_text();assert 'ERROR SUMMARY: 0 errors from 0 contexts (suppressed: 0 from 0)' in text and 'All heap blocks were freed' in text
obj=json.loads((objects/'status.json').read_text());assert len(obj)==4 and all(r['exit_code']==0 for r in obj)
known=json.loads((root/'evidence/controls/node-native-rev5-final-20261008/aarch64-warnings.json').read_text());by_diag={r['diagnostic']:r for r in known};shared=[]
for stem in ['macro-assembler','code-generator']:
 a=[l for l in (objects/(stem+'-original.log')).read_text().splitlines() if 'warning:' in l]
 b=[l for l in (objects/(stem+'-fixed.log')).read_text().splitlines() if 'warning:' in l];assert a==b
 for diagnostic in a:
  record=by_diag[diagnostic];assert record['same_diagnostic_as_qualified_x86'] and 'return-type' in diagnostic;shared.append(record)
verification=json.loads((prep/'verification.json').read_text());assert verification['patches']==25 and verification['zero_fuzz'] and verification['new_patches_zero_offset']
for directory,label in [(run,'constructors'),(objects,'translation-units'),(package,'package-helper'),(prep,'source-verification'),(root/'work/node-arm-operand-use-final-20261008','original-use-controls')]:
 dest=out/label;dest.mkdir(exist_ok=True)
 for p in directory.iterdir():
  if p.suffix in ['.log','.spec']:(dest/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
  elif p.suffix in ['.json','.cc','.py','.patch','.spec'] or p.name=='V8-LICENSE':shutil.copy2(p,dest/p.name)
initial=out/'initial-harness';initial.mkdir(exist_ok=True)
for p in (root/'work/node-arm-operand-use-20261008').glob('*.log'):(initial/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
for name in ['prepare-node-arm-operand-use-20261008.py','prepare-node-arm-operand-use-final-20261008.py','prepare-node-arm-initialization-20261008.py','check-node-arm-initialization-objects-20261008.py','check-node-arm-initialization-package-20261008.py','verify-node-arm-initialization-source-20261008.py','record-node-arm-initialization-20261008.py']:
 shutil.copy2(root/'work'/name,out/name)
(out/'unit-test-receipt.json').write_text(json.dumps({'source':'exec tool session 38429, completed exit 0','command':['python3','-B','-W','error','-m','unittest','discover','-s','tests'],'result':'Ran 224 tests in 2.978s; OK','limits':'Summary receipt from the completed tool result; raw unit stdout was not redirected to a file. The six dedicated command tests are included in the 224.'},indent=2)+'\n')
loader=importlib.util.spec_from_file_location('audit',root/'work/write-scoped-audit.py');audit=importlib.util.module_from_spec(loader);loader.loader.exec_module(audit)
passes={9:'New patch, C++ fixture, helper and tests carry 2026 copyright; upstream BSD notice is retained.',53:'Initialize the actual inactive members in both ARM64 operand classes before implicit value copies. No suppression, compiler-warning policy or production-access flag change.',54:'Member initializers cannot throw. Existing operand ownership and ABI are unchanged. Native use controls use unique_ptr; constructor fixtures destroy placement-created objects. All six final Valgrind runs free every allocation.',55:'Only per-object members are initialized. No mutable shared production state is added.',56:'NO_SHIFT, NO_EXTEND and unsigned zero use the actual enum/field types. The fixture verifies byte representations without evaluating invalid enums. Trivial-copyability assertions pass.',57:'Fixed-size member initialization adds no allocation or loop. Existing constructors with explicit initializers retain their selected values. No performance claim is made from the Og control.',58:'Original-source regression failures verify both missing-initialization paths. The package helper propagates constructor failure. Receipt validation continues rejecting malformed commands and the white-box access option is opt-in.',59:'RPM changelog and field comments explain the fixed invariant. Evidence documents the C++ language issue, deliberate original-source failures and native ARM/OBS follow-up.',61:'Private access is enabled only when compiling the white-box regression, never for runtime or other tests. Fixed argv arrays and offline containers are retained.',62:'459 constructor/copy checks and 3390 use checks pass at O2 and Og, normally and under Valgrind. Final RPM helper passes existing 4491 checks plus 459 new checks; all 224 packaging tests pass. All 25 patches and both architecture recipe expansions are verified.'}
audit.write(out/'audit.rst','ARM64 operand initialization fix audit','All 62 checks: 10 Pass, 52 N/A, 0 Fail for this focused fix and packaging integration. Full new native RPM build and runtime qualification remain required.',passes,'No Qore modules, DataProviders, QPP, JNI or new public API changes. Runtime patch adds no I/O, blocking or loops; finite standalone controls are outside a cancellable Qore program.')
record={'schema':1,'date':'2026-10-08','copyright':'Copyright 2026 Qore Technologies, s.r.o.','status':'Constructor defect fixed and focused qualification passed; full native package rebuild remains required.',
 'root_cause':'Immediate Operand constructors and the Operand-based immediate MemOperand constructor leave shift_, extend_ and shift_amount_ indeterminate. Guarded uses pass runtime checks, but implicit memberwise copies do not provide an unambiguous language guarantee for those fields. The fix gives each inactive field its natural sentinel/default without changing active semantics.',
 'standards_reference':{'url':'https://www.open-std.org/jtc1/sc22/wg21/docs/cwg_active.html#2264','title':'CWG 2264: Memberwise copying with indeterminate value','observed_status':'drafting, revision 120 dated 2026-05-31','interpretation':'This is not recorded as a proven harmless compiler warning. Initializing the actual fields removes the source ambiguity and the inputs behind the eight ARM diagnostics.'},
 'qualification':{'constructor_checks_per_execution':459,'use_checks_per_execution':3390,'modes':['O2 with release assertions','Og with release assertions'],'package_helper_existing_checks':4491,'package_helper_new_checks':459,'original_negative_controls':4,'final_valgrind_runs':6,'valgrind_errors':0,'all_allocations_freed':True,'packaging_unit_tests':224,'source_bundle':verification},
 'existing_translation_unit_diagnostics':shared,
 'limits':['The smaller original use controls and host-compiled ARM translation units do not reproduce the eight native compiler warnings. They demonstrate behavior and compilation, not disappearance of the native diagnostics. Native ARM compilation and execution remain required.',
 'The four unchanged host translation-unit exhaustive-enum warnings match previously qualified x86 sites and retain their existing approvals. No new diagnostic exception is requested for this fix.',
 'The white-box constructor fixture alone uses -fno-access-control to inspect private field representations; runtime compiler flags and all other test flags remain unchanged.',
 'Initial use control had a signedness warning in its own assertion, corrected with an explicit cast. Its O0 attempt also conflicted with retained FORTIFY flags; the final debug-oriented control uses Og with unchanged hardening. Original output is preserved.',
 'Expanded rpmspec output is retained as gzip with identical decompressed bytes, preserving generated trailing spaces without treating raw command output as edited source.',
 'The running OBS revision6 does not contain this new patch and has not been interrupted. Upload a new committed bundle only after the current builds finish. Publication remains disabled.'],
 'changed_files_sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['dependencies/nodejs24-arm-operand-initialization.patch','dependencies/nodejs24-arm-initialization-test.cc','dependencies/nodejs24-arm-header-test.py','dependencies/nodejs24-libnode.spec','tests/test_node_arm_header.py']},
 'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}}
(root/'evidence/node-arm-initialization-fix-20261008.json').write_text(json.dumps(record,indent=2)+'\n');print('Qualified initialization fix; evidence files',len(record['files_sha256']))
