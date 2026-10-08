# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,subprocess,xml.etree.ElementTree as ET
out=Path('results/grpc-credit-layout-upload-20261008');out.mkdir();source=Path('work/grpc-credit-layout-final-20261008');manifest=json.loads((source/'source-manifest.json').read_text())
assert manifest['commit']=='c008b67e10fe91c3c5268926f44f59c521babba5'
assert json.loads(Path('results/grpc-credit-layout-source-equivalence-20261008.json').read_text())['runtime_code_equal']
assert not any(json.loads(Path('results/grpc-credit-layout-candidate-status-20261008.json').read_text()).values())
osc=['osc','--setopt','http_retries=1','-A','https://api.opensuse.org','api'];base='/source/home:davidnichols:qore:testing/qore-grpc-module'
meta=subprocess.check_output([*osc,base+'/_meta']);(out/'metadata-before.xml').write_bytes(meta);m=ET.fromstring(meta)
assert [e.tag for e in m.find('publish')]==['disable']
assert {(e.attrib['repository'],e.attrib['arch']) for e in m.find('build') if e.tag=='enable'}=={(r,a) for r in ['Fedora_44','AlmaLinux_10','openSUSE_Leap_16.0'] for a in ['x86_64','aarch64']}
old=ET.fromstring(subprocess.check_output([*osc,base]));assert old.attrib['srcmd5']=='09c91d361c77c0e330b669058ac478f4'
with (out/'upload.log').open('x') as log:
 subprocess.run(['python3','-B','-W','error','tools/obs.py','upload','--project','home:davidnichols:qore:testing','--source',str(source),'--apply'],stdout=log,stderr=subprocess.STDOUT,check=True)
listing=subprocess.check_output([*osc,base]);(out/'source.xml').write_bytes(listing);remote=ET.fromstring(listing)
assert {e.attrib['name'] for e in remote.findall('entry')}==set(manifest['sources'])|{'source-manifest.json'}
for e in remote.findall('entry'):assert hashlib.md5((source/e.attrib['name']).read_bytes()).hexdigest()==e.attrib['md5']
after=subprocess.check_output([*osc,base+'/_meta']);(out/'metadata-after.xml').write_bytes(after);assert after==meta
(out/'manifest.json').write_bytes((source/'source-manifest.json').read_bytes())
print(remote.attrib,flush=True)
