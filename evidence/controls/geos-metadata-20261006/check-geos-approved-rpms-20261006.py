# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,os,subprocess
root=Path.cwd();outroot=root/'results/geos-approved-debugger-20261006';outroot.mkdir()
control=r'''# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,re,subprocess
binaries=[p for p in Path('payload/usr/lib/debug').rglob('*GEOSDataProvider*.debug') if not p.is_symlink()]
assert len(binaries)==1,binaries
binary=binaries[0];sections=subprocess.check_output(['readelf','-SW',str(binary)],text=True)
assert '.debug_names' not in sections and '.debug_info' in sections
options=['gdb','-q','-batch','-ex','set debuginfod enabled off','-ex','set substitute-path /usr/src/debug /fixture/payload/usr/src/debug','-ex','info functions _qaot_']
r=subprocess.run([*options,str(binary)],capture_output=True,text=True,check=True);source=location=None
for line in r.stdout.splitlines():
 if line.startswith('File '):source=line[5:].removesuffix(':')
 match=re.match(r'(\d+):\s+void _qaot_',line)
 if match and source:location=source+':'+match[1];break
assert location
r=subprocess.run([*options,'-ex','break '+location,'-ex','info breakpoints','-ex','list '+location,str(binary)],capture_output=True,text=True,check=True)
text=r.stdout+r.stderr;Path('gdb.log').write_text(text)
assert not re.search(r'warning:|No source file|No line |No symbol',text),text
assert 'Breakpoint 1 at ' in text and 'breakpoint     keep y' in text
assert any(re.match(r'\d+\s+[^\s]',l) for l in text.splitlines())
count=sum(bool(re.match(r'\d+:\s+void _qaot_',line)) for line in text.splitlines());assert count==108,count
Path('checks.json').write_text(json.dumps({'aot_functions':count,'breakpoint':location,'no_optional_name_index':True,'full_dwarf':True,'source_lookup':True},indent=2)+'\n')
print('PASS: packaged GEOS debug information, 108 functions, source lookup and breakpoint')
'''
(outroot/'control.py').write_text(control)
def run(target):
 out=outroot/target;out.mkdir();d=root/f'results/{target}-geos-metadata-candidate5-20261006';b=json.loads((d/'build.json').read_text());assert b['exit_code']==0;inputs={}
 for n,h in b['artifacts'].items():
  assert hashlib.sha256((d/n).read_bytes()).hexdigest()==h;inputs[n]=h
 cmd=['docker','run','--rm','--init','--network','none','--user',f'{os.getuid()}:{os.getgid()}','-v',str(out)+':/fixture','-v',str(outroot/'control.py')+':/control.py:ro','-v',str(d/'rpmbuild/RPMS')+':/rpms:ro','-w','/fixture',f'qore-rpm-keep:{target}-pdfium-installed-8','sh','-eu','-c','mkdir payload\ncd payload\nfor rpm in /rpms/*/*debug*.rpm; do rpm2cpio "$rpm" | cpio -idm --quiet; done\ncd ..\npython3 -B -W error /control.py\n']
 with (out/'tests.log').open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=240)
 (out/'status.json').write_text(json.dumps({'exit_code':r.returncode,'command':cmd,'inputs':inputs},indent=2)+'\n');return target,r.returncode
with ThreadPoolExecutor(max_workers=3) as p:print(dict(p.map(run,('fedora','leap','el10'))))
