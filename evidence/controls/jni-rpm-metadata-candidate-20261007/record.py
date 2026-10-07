# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import collections,gzip,hashlib,json,re,shutil,zipfile
root=Path.cwd();repo=root/'work/jni-rpm-integration-1';output=root/'evidence/controls/jni-rpm-metadata-candidate-20261007';output.mkdir(exist_ok=True)
source=json.loads((root/'work/jni-rpm-metadata-candidate-20261007/source-manifest.json').read_text());assert source['candidate']
for name,digest in source['packaging_overlay'].items():assert hashlib.sha256((repo/name).read_bytes()).hexdigest()==digest,name
records={};allowed={'QUnit','DataProvider','RestSchemaValidator','DataStreamUtil','Swagger','OpenApi3','RestClient','RestClientIo'}
for target in ('fedora','leap','el10'):
 build_path=root/f'results/{target}-jni-rpm-metadata-candidate-20261007';build=json.loads((build_path/'build.json').read_text());assert build['exit_code']==0 and build['source']==source
 for name,digest in build['artifacts'].items():
  with (build_path/name).open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==digest
 installed_path=root/f'results/{target}-jni-metadata-candidate-installed-2-20261007';installed=json.loads((installed_path/'status.json').read_text());assert installed['exit_code']==0 and all(s['exit_code']==0 for s in installed['steps'])
 artifact_path=root/f'results/{target}-jni-metadata-candidate-artifacts-20261007';artifact=json.loads((artifact_path/'status.json').read_text());assert artifact['exit_code']==0
 phases={}
 for phase in ('sdk','runtime'):
  text=(installed_path/(phase+'-tests.log')).read_text();counts=[tuple(map(int,x)) for x in re.findall(r'Ran (\d+) test cases?, (\d+) succeeded \((\d+) assertions?\)',text)]
  assert all(a==b for a,b,c in counts)
  assert (len(counts),sum(c[0] for c in counts),sum(c[2] for c in counts)) == ((37,632,8662) if phase=='sdk' else (23,478,4336))
  diagnostics=collections.Counter();lines=text.splitlines()
  for i,line in enumerate(lines):
   if line.startswith('warning:'):
    match=re.search(r"for feature '([^']+)'",line);assert match and match[1] in allowed and 'AOT-MODULE-STALE' in line,line
    assert re.search(r"optional module 'xml(?: >= 1\.3)?' was not available, but it is available now; rebuild the binary module$",line),line
    diagnostics[line]+=1
   elif line.startswith('WARNING in native method:'):
    assert target in ('leap','el10') and line=='WARNING in native method: JNI call made without checking exceptions when required to from CallObjectMethodV'
    assert '\tat sun.font.SunLayoutEngine.shape(' in lines[i+1]
    diagnostics[line]+=1
   elif re.search(r'(?i)^(?:warning|error|fatal):|Fontconfig error:',line):raise AssertionError((target,phase,line))
  phases[phase]={'suites':len(counts),'cases':sum(c[0] for c in counts),'assertions':sum(c[2] for c in counts),'diagnostics':dict(diagnostics)}
 records[target]={'build':build,'installed':installed,'artifacts':artifact,'phases':phases}
 for label,path in [('build',build_path/'build.log'),('sdk',installed_path/'sdk-tests.log'),('runtime',installed_path/'runtime-tests.log'),('artifacts',artifact_path/'check.log')]:
  (output/(target+'-'+label+'.log.gz')).write_bytes(gzip.compress(path.read_bytes(),mtime=0))
for name in ('qore-jni-module.spec','rpm/README.rst','rpm/install-layout.py','rpm/test_install_layout.py'):
 dest=output/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(repo/name,dest)
for name in ('jni-layout-helper-tests-20261007.log','jni-rpm-metadata-original-lint-20261007.log','jni-rpm-metadata-candidate-lint-20261007.log'):
 shutil.copy2(root/'results'/name,output/name)
assert 'Ran 24 tests' in (output/'jni-layout-helper-tests-20261007.log').read_text()
assert '15 errors, 97 warnings' in (output/'jni-rpm-metadata-original-lint-20261007.log').read_text()
assert '2 errors, 13 warnings' in (output/'jni-rpm-metadata-candidate-lint-20261007.log').read_text()
for name in ('build-jni-rpm-metadata-20261007.py','qualify-jni-metadata-installed-2-20261007.py','qualify-jni-metadata-artifacts-20261007.py','lint-jni-rpm-metadata-20261007.py'):
 shutil.copy2(root/'work'/name,output/name)
shutil.copy2(__file__,output/'record.py')
record={'schema':1,'copyright':'Copyright 2026 Qore Technologies, s.r.o.','date':'2026-10-07',
 'status':'Three candidate builds, six installed phases and three artifact checks pass. Metadata fixes eliminate 13 lint errors and 84 warnings. Remaining diagnostics are under review; the recipe is uncommitted and not uploaded.',
 'source_manifest':source,'targets':records,'helper_tests':24,
 'fixes':['Normalize nine staged launcher interpreters and generated runtime notice line endings; preserve modes, JARs, provenance and upstream Kotlin license bytes.',
          'Hardlink identical JAR payloads within each subpackage without changing classpaths or dependency versions.',
          'Name dynamically loaded font libraries by their provided ABI capabilities on openSUSE; retain the dependencies.',
          'Require the hardlink build tool even when documentation generation is disabled.'],
 'artifact_checks':['195 installed runtime JAR copies match pinned hashes; 176 notice/provenance records are retained.',
                    'Kotlin JARs match the verified build input and duplicate content shares inodes within its own subpackage.',
                    'All 22 AOT providers retain metadata and separate debug symbols/source; nine launchers have absolute interpreters.'],
 'remaining_lint':['2 exact java-21-openjdk-devel dependency reports for the Java/Kotlin compiler packages.',
                   '5 LicenseRef vocabulary warnings; complete notices are packaged.',
                   '4 vendor manifest Class-Path reports; Kotlin entries resolve. ODS vendor manifests contain historical/optional names needing further review before an exception is proposed.',
                   '2 catalog ownership-directory warnings; prior approvals for other packages do not automatically extend to JNI.',
                   '2 generated Source archive URL warnings in local rpmlint.'],
 'limits':['The first installed harness omitted AUTOPKGTEST_TMP for the added compiler check. It failed after the original suites and consumer passed; only the second complete runs qualify the candidate.',
           'Reported suite totals include existing external-service skips and cases without assertions.',
           'No new lint or build diagnostic exception is approved by this record. Canonical committed-source/native builds and final core22 combined qualification remain required.'],
 'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.rglob('*')) if p.is_file()}}
(root/'evidence/jni-rpm-metadata-candidate-20261007.json').write_text(json.dumps(record,indent=2)+'\n')
print('JNI metadata candidate verified; remaining lint review explicitly open')
