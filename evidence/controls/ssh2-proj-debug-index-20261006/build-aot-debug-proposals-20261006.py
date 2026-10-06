# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib,io,json,re,shutil,subprocess,tarfile,sys
sys.path.insert(0,'tools');from packaging import obs_changelog
root=Path.cwd()
paths={'proj':['ProjGeos/ProjGeos.qmod'],'ssh2':['SftpClientDataProvider/SftpClientDataProvider.qmod','SftpPoller.qmod','SftpPollerUtil.qmod','Ssh2Connections.qmod']}
for mod in paths:
 source=root/f'work/{mod}-debug-index-proposal-20261006';base=root/('work/proj-metadata2-candidate-20261006' if mod=='proj' else 'work/ssh2-metadata-canonical-20261006');shutil.copytree(base,source)
 manifest=json.loads((source/'source-manifest.json').read_text());spec=source/manifest['spec'];text=spec.read_text()
 text=text.replace('BuildRequires: gcc-c++\n','BuildRequires: gcc-c++\nBuildRequires: binutils\nBuildRequires: python3\n%if 0%{?suse_version}\nBuildRequires: debugedit >= 5.1\n%endif\n')
 text=text.replace('%if %{with tests}\nBuildRequires: python3\n','%if %{with tests}\n')
 if mod=='ssh2':text=text.replace('Release: 3%{?dist}','Release: 4%{?dist}')
 line='find %{buildroot}%{_libdir}/qore-modules -type f -name \'*.qmod\' -exec chmod 755 {} +\n';assert line in text
 action='# Retain full DWARF and source; distribution GDB ignores LLVM\'s optional index.\n'
 for path in paths[mod]:action+='python3 %{qore_rpm_helper} %{buildroot} objcopy --remove-section=.debug_names \\\n  %{buildroot}%{_libdir}/qore-modules/'+path+'\n'
 text=text.replace(line,line+action)
 check='''python3 -B -W error - <<'PYTHON'
import importlib.util
from pathlib import Path
import subprocess
spec = importlib.util.spec_from_file_location('aot', '%{qore_rpm_helper}')
aot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(aot)
for relative in PATHS:
    binary = Path('%{buildroot}%{_libdir}/qore-modules') / relative
    assert b'QAMD' in aot.read_trailers(binary), 'AOT metadata lost during RPM processing'
    sections = subprocess.check_output(['readelf', '-SW', str(binary)], text=True)
    assert '.gnu_debuglink' in sections, 'Missing separate AOT debug information'
    assert '.debug_names' not in sections and '.debug_info' not in sections
PYTHON
'''.replace('PATHS',repr(paths[mod]))
 text=text.replace('%check\n%if %{with tests}\n','%check\n%if %{with tests}\n'+check)
 if mod=='ssh2':text=text.replace('%changelog\n','%changelog\n* Tue Oct 06 2026 David Nichols <david@qore.org> - 2.0.0-4\n- Preserve full AOT debugging without unsupported optional LLVM name indexes.\n\n')
 else:text=text.replace('- Remove unused configure options and unshipped optional Java generation.','- Remove unused configure options and unshipped optional Java generation.\n- Preserve full AOT debugging without unsupported optional LLVM name indexes.')
 spec.write_text(text);changes=source/(manifest['name']+'.changes');changes.write_text(obs_changelog(text))
 # Explicit candidate archive overlay, never eligible for OBS upload.
 archive=source/(manifest['name']+'-'+manifest['version']+'.tar.xz');buffer=io.BytesIO();prefix=manifest['name']+'-'+manifest['version']+'/'
 with tarfile.open(archive) as old,tarfile.open(fileobj=buffer,mode='w:xz',format=tarfile.PAX_FORMAT) as new:
  for member in old.getmembers():
   if member.name==prefix+manifest['spec']:
    data=text.encode();member.size=len(data);new.addfile(member,io.BytesIO(data))
   else:new.addfile(member,old.extractfile(member) if member.isfile() else None)
 archive.write_bytes(buffer.getvalue());manifest['candidate']=True;manifest['proposal']='Unapproved SSH2/PROJ extension of the Oracle/PDFium debugger configuration; qualification only.'
 for p in (spec,archive,changes):manifest['sources'][p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 manifest.setdefault('packaging_overlay',{})[spec.name]=manifest['sources'][spec.name]
 (source/'source-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
def build(case):
 mod,target=case;images=json.loads((root/f'results/{mod}-sdk21-debugedit51-images-20261006.json').read_text())
 with (root/f'results/{target}-{mod}-debug-index-proposal-driver-20261006.log').open('x') as log:r=subprocess.run(['python3','-B','tools/build-local.py','--source',f'work/{mod}-debug-index-proposal-20261006','--image',images[target],'--output',f'results/{target}-{mod}-debug-index-proposal-20261006','--jobs','2'],stdout=log,stderr=subprocess.STDOUT)
 return mod+'-'+target,r.returncode
with ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(build,[(mod,target) for mod in paths for target in ('fedora','leap','el10')]))
(root/'results/aot-debug-proposal-status-20261006.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
