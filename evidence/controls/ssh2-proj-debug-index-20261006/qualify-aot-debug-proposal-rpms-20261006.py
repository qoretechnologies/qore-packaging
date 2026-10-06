# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,subprocess
root=Path.cwd();outroot=root/'results/aot-debug-index-proposal-installed-20261006';outroot.mkdir()
control=r'''from pathlib import Path
import json,re,subprocess
records=[]
for binary in sorted(Path('payload/usr/lib/debug').rglob('*.debug')):
 if binary.is_symlink() or binary.name.startswith(('ssh2-api-','proj-api-')):continue
 sections=subprocess.check_output(['readelf','-SW',str(binary)],text=True);assert '.debug_names' not in sections;assert '.debug_info' in sections and '.debug_line' in sections
 base=['gdb','-q','-batch','-ex','set debuginfod enabled off','-ex','set substitute-path /usr/src/debug /fixture/payload/usr/src/debug','-ex','info functions _qaot_']
 r=subprocess.run([*base,str(binary)],capture_output=True,text=True,check=True);assert not r.stderr,r.stderr
 source=None;location=None
 for line in r.stdout.splitlines():
  if line.startswith('File '):source=line[5:].removesuffix(':')
  match=re.match(r'(\d+):\s+void _qaot_',line)
  if match and source:location=source+':'+match[1];break
 assert location,(binary,r.stdout)
 r=subprocess.run([*base,'-ex','break '+location,'-ex','info breakpoints','-ex','list '+location,str(binary)],capture_output=True,text=True,check=True);assert not r.stderr,r.stderr
 assert 'Breakpoint 1 at ' in r.stdout and 'breakpoint     keep y' in r.stdout,r.stdout
 assert any(re.match(r'\d+\s+[^\s]',l) for l in r.stdout.splitlines()),r.stdout
 Path(binary.name+'.gdb.txt').write_text(r.stdout)
 records.append({'binary':str(binary),'breakpoint_source_location':location,'full_dwarf':True,'no_optional_name_index':True,'gdb_stderr':''})
assert len(records)==5,len(records)
Path('checks.json').write_text(json.dumps(records,indent=2)+'\n');print('PASS: all five proposal AOT debug RPM files support source and breakpoint lookup without diagnostics')
'''
(outroot/'control.py').write_text(control)
def run(target):
 out=outroot/target;out.mkdir();inputs={}
 for mod in ('ssh2','proj'):
  directory=root/f'results/{target}-{mod}-debug-index-proposal-20261006';build=json.loads((directory/'build.json').read_text());assert build['exit_code']==0
  for name,digest in build['artifacts'].items():
   if '/RPMS/' in name and '-debug' in name:
    path=directory/name;assert hashlib.sha256(path.read_bytes()).hexdigest()==digest;inputs[f'{mod}/{path.name}']=digest
 script='set -eu\nmkdir payload\ncd payload\nfor rpm in /ssh2/*/*debug*.rpm /proj/*/*debug*.rpm; do rpm2cpio "$rpm" | cpio -idm --quiet; done\ncd ..\npython3 -B -W error /control.py\n'
 cmd=['docker','run','--rm','--init','--network','none','--user',f'{os.getuid()}:{os.getgid()}','-v',str(out)+':/fixture','-v',str(outroot/'control.py')+':/control.py:ro','-v',str(root/f'results/{target}-ssh2-debug-index-proposal-20261006/rpmbuild/RPMS')+':/ssh2:ro','-v',str(root/f'results/{target}-proj-debug-index-proposal-20261006/rpmbuild/RPMS')+':/proj:ro','-w','/fixture',f'qore-rpm-keep:{target}-pdfium-installed-8','sh','-ec',script]
 with (out/'tests.log').open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 (out/'status.json').write_text(json.dumps({'exit_code':r.returncode,'command':cmd,'inputs':inputs},indent=2)+'\n');return target,r.returncode
with ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(run,('fedora','leap','el10')))
(outroot/'status.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
