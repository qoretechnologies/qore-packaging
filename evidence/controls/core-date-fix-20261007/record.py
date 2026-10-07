# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip
import hashlib
import json
import shutil
import subprocess

root=Path.cwd(); main=root.parent/'qore'; checkout=root/'work/checkouts/qore-documentation-sdk-20261006'
commit='298fdb595c982b6c621cdabeed163198639dd696'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=main,text=True).strip()==commit
backport=subprocess.check_output(['git','rev-parse','HEAD'],cwd=checkout,text=True).strip()
assert backport.startswith('d740af66e')
assert not subprocess.check_output(['git','status','--porcelain'],cwd=checkout)
qualified=json.loads((root/'results/core-date-final-verification-20261007.json').read_text())
assert qualified['result']=='pass'
for name,digest in qualified['source_sha256'].items():
    assert hashlib.sha256((main/name).read_bytes()).hexdigest()==digest,name
for branch,source in [('develop',commit),('rpm/documentation-sdk-20261006',backport)]:
    assert subprocess.check_output(['git','ls-remote','origin','refs/heads/'+branch],cwd=main,text=True).split()[0]==source
neg=json.loads((root/'results/core-date-rpm-negative-final-20261007/status.json').read_text())
assert len(neg)==3 and all(row['old_library_expected_failure'] and row['exit_code']==0 for row in neg)
assert (root/'results/core-relative-sign-final-driver-20261007.log').read_text().startswith('PASS: original fails; 679 cases')
backport_result=json.loads((root/'results/core-date-backport-20261007/status.json').read_text())
assert all(row['exit_code']==0 for row in backport_result['steps'])
out=root/'evidence/controls/core-date-fix-20261007';out.mkdir(exist_ok=True)
for directory in ['core-date-add-final3-tests-20261007','core-date-rpm-negative-final-20261007',
                  'core-date-conversion-20261007','core-relative-sign-matrix-final-20261007',
                  'core-date-language-valgrind2-20261007','core-date-pcre-debug-20261007',
                  'core-date-docs-20261007','core-date-docs2-20261007','core-date-backport-20261007']:
    source=root/'results'/directory
    for path in source.rglob('*'):
        if not path.is_file() or path.suffix not in ('.log','.json','.cpp'):continue
        dest=out/directory/path.relative_to(source);dest.parent.mkdir(parents=True,exist_ok=True)
        if path.suffix=='.log':
            dest=dest.with_suffix('.log.gz');dest.write_bytes(gzip.compress(path.read_bytes(),mtime=0))
        else: shutil.copy2(path,dest)
for name in ['core-date-final-verification-20261007.json','core-date-final2-harness-correction-20261007.json',
             'core-date-memory-profile-correction-20261007.json','core-date-stale-qualifier-cancellation-20261007.json']:
    shutil.copy2(root/'results'/name,out/name)
for name in ['qualify-core-date-add-final3-running-source-20261007.py','verify-core-date-final-20261007.py',
             'check-core-date-rpm-negative-final-20261007.py','check-core-date-conversion-20261007.py',
             'core-relative-sign-control-20261007.cpp','check-relative-sign-control-final-20261007.py',
             'check-date-language-valgrind2-20261007.py','debug-date-pcre-20261007.py',
             'check-core-date-docs-20261007.py','check-core-date-docs2-20261007.py',
             'check-core-date-backport-20261007.py']:
    shutil.copy2(root/'work'/name,out/name)
shutil.copy2(main/'examples/test/qore/vars/audits/date-add-native.rst',out/'main-audit.rst')
shutil.copy2(checkout/'examples/test/qore/vars/audits/date-add-native.rst',out/'rpm-branch-audit.rst')
shutil.copy2(Path(__file__),out/'record.py')
record={'schema':1,'date':'2026-10-07','copyright':'Copyright 2026 Qore Technologies, s.r.o.',
        'status':'Both date defects fixed, audited, committed and pushed to develop and the isolated RPM source branch. Complete updated RPM qualification remains required.',
        'main_commit':commit,'rpm_branch_commit':backport,
        'root_causes':['DateTime::add passed the right operand pointer to a private date constructor through bool conversion, replacing it with an empty relative date.',
                       'Pairwise relative-time normalization missed opposite signs separated by zero seconds/minutes, producing unequal representations for equal elapsed times.'],
        'fixes':['Dereference the operand, make the private bool constructor explicit, and guard allocated results with unique_ptr.',
                 'Normalize the bounded sub-hour remainder with int64 arithmetic and move a conflicting hour sign toward zero before splitting lower units.'],
        'qualification':qualified,'backport':backport_result,
        'negative_controls':'The exact committed native regression fails with the expected first-case wrong result against all three installed core22 SDKs; the original relative-time header fails the independent boundary control.',
        'existing_approvals':['evidence/core-close-rpm-qualification-20261002.json','evidence/zmq-pcre2-diagnostic-20261006.json'],
        'limits':['The RPM-branch focused build reuses the qualified identical date implementation; full new RPM builds, native OBS and installed-package qualification remain required.',
                  'No new diagnostic exception, memory suppression or runtime workaround is introduced.',
                  'Earlier harness failures and the missing local XML module path are retained and explained in the audit. The raw running qualifier has a singular/plural summary bug; final verification validates successful child exit codes and both summary forms.'],
        'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.rglob('*')) if p.is_file()}}
(root/'evidence/core-date-fix-20261007.json').write_text(json.dumps(record,indent=2)+'\n')
print('Recorded verified date fix commits, all positive/negative controls, audit and existing diagnostic scope')
