# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,re,subprocess
root=Path.cwd();build=root/'results/leap-nodejs24-canonical-final-20261007';source='/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
record=json.loads((build/'build.json').read_text());assert record['exit_code']==0
output=root/'results/node-obs-full-check-20261008';output.mkdir()
so=build/source.removeprefix('/work/')/'out/Release/libnode.so.137'
with so.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
recipe=(root/'dependencies/nodejs24-libnode.spec').read_text();check=recipe.split('%check\n',1)[1].split('\n%post ',1)[0];image=record['image']
optflags=subprocess.check_output(['docker','run','--rm','--network','none',image,'rpm','--eval','%{optflags}'],text=True).strip()
check=check.replace('%{optflags}',optflags).replace('%{soname}','137').replace('%{_smp_build_ncpus}','2').replace('%make_build','make -j2')
for number,name in re.findall(r'^Source(\d+):\s+(\S+)$',recipe,re.M):
 if '://' not in name:check=check.replace('%{SOURCE'+number+'}','/sources/'+name)
assert '%{' not in check;(output/'check.sh').write_text('set -eu\n'+check)
setup='''from pathlib import Path
import pwd
Path('/etc/hosts').write_text('127.0.0.1 obs-fixture\\n'+Path('/fixtures/netcfg-hosts').read_text())
Path('/etc/nsswitch.conf').write_text('passwd: files\\ngroup: files\\nhosts: files dns\\n')
for name in ['/etc/passwd','/etc/group']:
 p=Path(name);p.write_text(''.join(l for l in p.read_text().splitlines(True) if not l.startswith('nobody:')))
try:
 pwd.getpwnam('nobody')
except KeyError:
 pass
else:
 raise AssertionError('missing-user control still resolves nobody')
'''
(output/'setup.py').write_text(setup)
script='''set -eu
rpm -q netcfg
rpm -e libnode-devel abseil-cpp-devel protobuf-devel
test ! -e /usr/include/absl/synchronization/mutex.h
test ! -e /usr/lib64/libnode.so
python3 /control/setup.py
exec setpriv --reuid=1019 --regid=100 --clear-groups bash /control/check.sh
'''
fixtures=root/'results/node-obs-fixtures2-20261008'
cmd=['docker','run','--rm','--init','--network','none','-v',str(build)+':/work','-v',str(root/'dependencies')+':/sources:ro','-v',str(output)+':/control','-v',str(fixtures)+':/fixtures:ro','-v',str(fixtures/'fixed.js')+':'+source+'/test/parallel/test-process-euid-egid.js:ro','-w',source,image,'sh','-c',script]
with (output/'check.log').open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
with so.open('rb') as f:after=hashlib.file_digest(f,'sha256').hexdigest()
(output/'status.json').write_text(json.dumps({'command':cmd,'exit_code':r.returncode,'built_library_sha256_before':digest,'built_library_sha256_after':after,'recipe_sha256':hashlib.sha256(recipe.encode()).hexdigest()},indent=2)+'\n')
assert digest==after;r.check_returncode()
print('Complete updated Node %check passed with netcfg hosts and no nobody account.',flush=True)
