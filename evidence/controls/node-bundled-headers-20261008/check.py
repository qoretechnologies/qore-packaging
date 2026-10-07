# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,re,subprocess
root=Path.cwd();build=root/'results/leap-nodejs24-canonical-final-20261007';source='/work/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
record=json.loads((build/'build.json').read_text());assert record['exit_code']==0
output=root/'results/node-bundled-headers-check-20261007';output.mkdir()
so=build/source.removeprefix('/work/')/'out/Release/libnode.so.137';assert so.is_file() and not so.with_name('libnode.so').exists()
with so.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
recipe=(root/'dependencies/nodejs24-libnode.spec').read_text();check=recipe.split('%check\n',1)[1].split('\n%post ',1)[0]
image=record['image']
optflags=subprocess.check_output(['docker','run','--rm','--network','none',image,'rpm','--eval','%{optflags}'],text=True).strip()
sources=dict(re.findall(r'^Source(\d+):\s+(\S+)$',recipe,re.M))
check=check.replace('%{optflags}',optflags).replace('%{soname}','137').replace('%{_smp_build_ncpus}','2').replace('%make_build','make -j2')
for number,name in sources.items():
 if '://' not in name:check=check.replace('%{SOURCE'+number+'}','/sources/'+name)
assert '%{' not in check
(output/'check.sh').write_text('set -eu\n'+check)
script='''set -eu
rpm -q libnode-devel abseil-cpp-devel protobuf-devel
rpm -e libnode-devel abseil-cpp-devel protobuf-devel
if rpm -q libnode-devel; then exit 1; fi
if rpm -q abseil-cpp-devel; then exit 1; fi
test ! -e /usr/include/absl/synchronization/mutex.h
test ! -e /usr/lib64/libnode.so
exec setpriv --reuid=1019 --regid=100 --clear-groups bash /control/check.sh
'''
cmd=['docker','run','--rm','--init','--network','none','-v',str(build)+':/work','-v',str(root/'dependencies')+':/sources:ro','-v',str(output)+':/control','-w',source,image,'sh','-c',script]
with (output/'check.log').open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
with so.open('rb') as f:after=hashlib.file_digest(f,'sha256').hexdigest()
(output/'status.json').write_text(json.dumps({'command':cmd,'exit_code':r.returncode,'built_library_sha256_before':digest,'built_library_sha256_after':after,'recipe_sha256':hashlib.sha256(recipe.encode()).hexdigest()},indent=2)+'\n')
assert digest==after
r.check_returncode()
print('Complete Node %check passes without installed Node or Abseil development packages',flush=True)
