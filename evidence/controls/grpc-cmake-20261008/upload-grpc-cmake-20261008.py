# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,subprocess,xml.etree.ElementTree as ET
out=Path('results/grpc-cmake-upload-20261008');out.mkdir();source=Path('work/grpc-cmake-final-20261008');manifest=json.loads((source/'source-manifest.json').read_text())
assert manifest['commit']=='5f6cc3469e82f98c78c00e32f07d34c41a03a0c5'
assert json.loads(Path('results/grpc-cmake-source-equivalence-20261008.json').read_text())['code_and_recipe_equal']
osc=['osc','--setopt','http_retries=1','-A','https://api.opensuse.org','api'];base='/source/home:davidnichols:qore:testing/qore-grpc-module'
meta=subprocess.check_output([*osc,base+'/_meta']);(out/'metadata-before.xml').write_bytes(meta);m=ET.fromstring(meta)
assert [e.tag for e in m.find('publish')]==['disable']
assert {(e.attrib['repository'],e.attrib['arch']) for e in m.find('build') if e.tag=='enable'}=={(r,a) for r in ['Fedora_44','AlmaLinux_10','openSUSE_Leap_16.0'] for a in ['x86_64','aarch64']}
old=ET.fromstring(subprocess.check_output([*osc,base]));assert old.attrib['srcmd5']=='48243e31b67baef88ffe0c0b3dbab59b'
with (out/'upload.log').open('x') as log:
 subprocess.run(['python3','-B','-W','error','tools/obs.py','upload','--project','home:davidnichols:qore:testing','--source',str(source),'--apply'],stdout=log,stderr=subprocess.STDOUT,check=True)
listing=subprocess.check_output([*osc,base]);(out/'source.xml').write_bytes(listing);remote=ET.fromstring(listing)
assert {e.attrib['name'] for e in remote.findall('entry')}==set(manifest['sources'])|{'source-manifest.json'}
for e in remote.findall('entry'):assert hashlib.md5((source/e.attrib['name']).read_bytes()).hexdigest()==e.attrib['md5']
after=subprocess.check_output([*osc,base+'/_meta']);(out/'metadata-after.xml').write_bytes(after);assert after==meta
(out/'manifest.json').write_bytes((source/'source-manifest.json').read_bytes())
print(remote.attrib,flush=True)
