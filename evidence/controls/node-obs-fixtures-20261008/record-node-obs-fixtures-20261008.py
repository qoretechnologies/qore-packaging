# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip,hashlib,importlib.util,json,re,shutil,xml.etree.ElementTree as ET
root=Path.cwd();run=root/'results/node-obs-fixtures2-20261008';out=root/'evidence/controls/node-obs-fixtures-20261008';out.mkdir(exist_ok=True)
status=json.loads((run/'status.json').read_text());counts={}
for case in status:
 log=(run/(case['name']+'.log')).read_text();bad=re.findall(r'^not ok \d+ (\S+)',log,re.M);good=re.findall(r'^ok \d+ (\S+)',log,re.M)
 expected=6 if case['name']=='original-minimal' else 1 if case['name']=='original-netcfg' else 0
 assert len(bad)==expected and len(bad)+len(good)==6
 assert case['exit_code']==int(bool(expected))
 if expected==1:assert bad==['parallel/test-process-euid-egid']
 assert '# skip' not in log.lower()
 counts[case['name']]={'passed':len(good),'expected_baseline_failures':bad}
negative=(run/'assertion-negative.log').read_text();assert len(re.findall(r'^PASS:',negative,re.M))==7
assert json.loads((run/'assertion-negative.json').read_text())['exit_code']==0
log=(root/'results/node-obs-fixtures-tools-tests-20261008.log').read_text();assert re.search(r'Ran 218 tests in [\d.]+s\n\nOK\s*$',log)
for arch in ['x86_64','aarch64']:
 p=root/f'results/node-netcfg-proposed-buildinfo-{arch}-20261008.xml';tree=ET.fromstring(p.read_bytes())
 assert not tree.findall('error')
 deps=[n for n in tree.findall('bdep') if n.get('name')=='netcfg'];assert len(deps)==1 and deps[0].get('version')=='11.6'
 (out/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
for p in run.iterdir():
 if p.suffix=='.rpm':continue
 if p.suffix=='.log':(out/(p.name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
 else:shutil.copy2(p,out/p.name)
for name in ['check-node-obs-fixtures-20261008.py','check-node-obs-fixtures2-20261008.py','node-credential-assertion-control-20261008.js','check-node-obs-full-20261008.py','record-node-obs-fixtures-20261008.py']:shutil.copy2(root/'work'/name,out/name)
(out/'tools-tests.log.gz').write_bytes(gzip.compress(log.encode(),mtime=0))
for name in ['nodejs24-libnode.spec','nodejs24-libnode.rst','nodejs24-credential-test-error.patch']:shutil.copy2(root/'dependencies'/name,out/name)
node_config=json.loads((root/'dependencies/sources.json').read_text())['nodejs24-libnode'];(out/'source-config.json').write_text(json.dumps(node_config,indent=2)+'\n')
# Preserve the exact failed native log, binding it to verified OBS revision5.
failed=root/'results/node-native-rev5-live-20261008/x86_64-snapshot2.log'
assert 'Bad exit status' in failed.read_text() and len(re.findall(r'^\[\s*\d+s\] not ok ',failed.read_text(),re.M))==6
(out/'native-x86_64-rev5.log.gz').write_bytes(gzip.compress(failed.read_bytes(),mtime=0))
loader=importlib.util.spec_from_file_location('audit',root/'work/write-scoped-audit.py');audit=importlib.util.module_from_spec(loader);loader.loader.exec_module(audit)
passes={9:'New patch and qualification controls carry 2026 copyright.',53:'The recipe declares the distribution package required by unchanged network tests. The credential test now matches structured errors. No skip, retry, suppression or production runtime change.',54:'Container fixtures are discarded on exit; subprocess results are recorded and verified. No C++ allocation or runtime ownership change.',55:'Each paired control uses a separate container. The source overlay is read-only; only disposable hosts/account fixtures are changed.',56:'Credential assertions validate code and message separately; negative controls reject unrelated codes/messages and missing exceptions.',57:'The change adds one small build dependency and no installed runtime cost.',58:'Minimal controls reproduce all six native failures; adding only netcfg resolves exactly five. The remaining stale credential assertion is corrected and tested in both account states.',59:'Dependency guide explains dual-stack localhost requirements and structured missing-user errors. Spec changelog records both changes.',61:'No host account or resolver file is modified. Fixture scripts edit only throwaway-container /etc paths; API requests do not expose credentials.',62:'All 12 corrected real test results pass, as do seven assertion controls and 218 packaging tests. Both OBS architectures resolve netcfg. The qualified hosts file is byte-identical to the resolved Leap RPM; the patch applies without fuzz or offset.'}
audit.write(out/'audit.rst','Node native fixture fixes audit','Scope: openSUSE build dependency and JavaScript test assertion, paired controls and documentation. All 62 checks: 10 Pass, 52 N/A, 0 Fail. Complete local %check is running; native build and installed package gates remain required.',passes,'No corresponding Qore module/QPP/DataProvider/JNI, C++ production or Qore-language test change in this scope.')
record={'schema':1,'date':'2026-10-08','copyright':'Copyright 2026 Qore Technologies, s.r.o.','status':'Six native x86_64 failures root-caused; test prerequisite and assertion corrections pass focused qualification. Complete local check and native RPM qualification remain required.','native_source':{'project':'home:davidnichols:qore:testing','package':'nodejs24-libnode','revision':'5','srcmd5':'4deae1c099435cb9b5dfa52d0f8f45a2'},'root_causes':['Without netcfg, OBS creates an IPv4-only hosts file. Four tests pass a family-6 address object without a host field, triggering an IPv6 localhost lookup; a fifth test requires a reverse name for ::1.','The unprivileged effective-user test allows a missing nobody account but matches the old Error.toString form; the structured ERR_UNKNOWN_CREDENTIAL annotation fails that regex.'],'fixes':['Declare netcfg as an openSUSE build prerequisite, preserving both localhost address families.','Match the allowed credential error code and message separately.'],'matrix':counts,'fixed_results':12,'assertion_controls':7,'tooling_tests':218,'buildinfo_architectures':['x86_64','aarch64'],'complete_check':'results/node-obs-full-check-20261008/status.json (running when this record was created)','limits':['Native rev5 ARM remains in progress; no native success or publication is claimed.','The first account-removal control still resolved systemds synthetic nobody user. The final controls select the files provider and assert the actual account lookup result before running tests.','Runtime source and compiler flags are unchanged. Existing native compiler diagnostic review remains a separate gate.'],'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir()) if p.is_file()}}
(root/'evidence/node-obs-fixtures-20261008.json').write_text(json.dumps(record,indent=2)+'\n')
print('Recorded paired six-failure reproduction, 12 corrected results, seven negative/positive assertions, 218 tools tests and both native dependency resolutions.')
