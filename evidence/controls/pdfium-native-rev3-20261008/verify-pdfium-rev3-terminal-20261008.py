# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,json,xml.etree.ElementTree as E,re,hashlib
out=Path('results/pdfium-native-rev3-20261008');expected='a815379d22cf1df53054e4fb1cd735f8'
cmd=['osc','api','/build/home:davidnichols:qore:testing/_result?package=qore-pdfium'];p=subprocess.run(cmd,capture_output=True,check=True);(out/'terminal-results.xml').write_bytes(p.stdout)
root=E.fromstring(p.stdout);states={(r.get('repository'),r.get('arch')):s.get('code') for r in root for s in r.findall('status')};assert len(states)==6 and all(x=='succeeded' for x in states.values()),states
sources=subprocess.run(['osc','api','/source/home:davidnichols:qore:testing/qore-pdfium'],capture_output=True,check=True).stdout;(out/'terminal-source.xml').write_bytes(sources);assert E.fromstring(sources).get('srcmd5')==expected

def verify(target):
 repo,arch=target;d=out/(repo+'-'+arch);base='/build/home:davidnichols:qore:testing/'+repo+'/'+arch+'/qore-pdfium'
 for suffix,name in [('/_history?limit=1','history-terminal.xml'),('/_buildinfo','buildinfo-terminal.xml'),('','binaries.xml')]:
  p=subprocess.run(['osc','api',base+suffix],capture_output=True,check=True);(d/name).write_bytes(p.stdout)
 history=E.parse(d/'history-terminal.xml').getroot();assert len(history)==1 and history[0].get('srcmd5')==expected,history.attrib
 assert history[0].get('rev')=='3'
 for name in ['buildinfo-before.xml','buildinfo-terminal.xml']:
  assert E.parse(d/name).getroot().findtext('srcmd5')==expected
 log=(d/'build.log').read_text(errors='replace');assert re.findall(r'\[  PASSED  \] (\d+) tests\.',log)==['989','830']
 assert 'finished "build qore-pdfium.spec"' in log
 assert 'Build argument has no effect' not in log
 diagnostics=[l for l in log.splitlines() if re.search(r'warning:|error:|WARNING| W: | E: ',l)]
 if repo=='openSUSE_Leap_16.0':
  assert len(diagnostics)==1 and 'warning: %post(polkit-default-privs-1550+20260709.b1b58aa-160000.1.1.noarch) scriptlet failed, exit status 2' in diagnostics[0],diagnostics
 else:assert not diagnostics,diagnostics
 bins=[e.attrib for e in E.parse(d/'binaries.xml').getroot() if e.get('filename','').endswith('.rpm')]
 assert len(bins)==5,(target,bins)
 result={'repository':repo,'architecture':arch,'status':'succeeded','history':history[0].attrib,'unit_tests':989,'embedder_tests':830,'c_api_check':'passed','compiler_or_gn_diagnostics':0,'bootstrap_diagnostics':diagnostics,'rpm_outputs':bins,'log_sha256':hashlib.sha256((d/'build.log').read_bytes()).hexdigest()}
 (d/'verified.json').write_text(json.dumps(result,indent=2)+'\n');print(repo,arch,'verified',flush=True);return repo+'/'+arch,result
with ThreadPoolExecutor(max_workers=6) as pool:r=dict(pool.map(verify,states))
(out/'verified-summary.json').write_text(json.dumps(r,indent=2)+'\n')
