# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,json,xml.etree.ElementTree as E,re
out=Path('results/pdfium-native-rev3-20261008');out.mkdir(exist_ok=False)
expected='a815379d22cf1df53054e4fb1cd735f8'
targets=[(r,a) for r in ['Fedora_44','openSUSE_Leap_16.0','AlmaLinux_10'] for a in ['x86_64','aarch64']]
def collect(target):
 repo,arch=target;d=out/(repo+'-'+arch);d.mkdir();base='/build/home:davidnichols:qore:testing/'+repo+'/'+arch+'/qore-pdfium'
 def get(suffix,name):
  command=['osc','--setopt','http_retries=1','api',base+suffix]
  with (d/name).open('wb') as log,(d/(name+'.stderr')).open('wb') as err:r=subprocess.run(command,stdout=log,stderr=err)
  assert r.returncode==0,(target,name,r.returncode)
 get('/_buildinfo','buildinfo-before.xml')
 info=E.parse(d/'buildinfo-before.xml').getroot();assert info.findtext('srcmd5')==expected
 # OBS streams the current build to completion. No timer or polling loop.
 get('/_log','build.log')
 get('/_history?limit=1','history.xml')
 get('/_status','status.xml')
 status=E.parse(d/'status.xml').getroot();history=E.parse(d/'history.xml').getroot()
 text=(d/'build.log').read_text(errors='replace')
 passed=re.findall(r'\[  PASSED  \] (\d+) tests\.',text)
 diagnostics=[line for line in text.splitlines() if re.search(r'warning:|error:|WARNING| W: | E: |getbinaries|Build argument has no effect',line)]
 result={'repository':repo,'architecture':arch,'expected_srcmd5':expected,'status':status.attrib,'history':[e.attrib for e in history],'passed_test_groups':passed,'diagnostics':diagnostics,'finished':'finished "build qore-pdfium.spec"' in text}
 if status.get('code')=='succeeded':
  assert passed==['989','830'],result
  assert result['finished'],result
  assert history[0].get('srcmd5')==expected,result
 (d/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(repo,arch,status.attrib,passed,flush=True)
 return repo+'/'+arch,result
with ThreadPoolExecutor(max_workers=6) as pool:result=dict(pool.map(collect,targets))
(out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
