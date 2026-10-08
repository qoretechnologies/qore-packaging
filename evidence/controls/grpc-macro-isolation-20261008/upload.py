# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,subprocess,xml.etree.ElementTree as ET
out=Path('results/grpc-macro-upload-20261008');out.mkdir();source=Path('work/grpc-macro-source-20261008');manifest=json.loads((source/'source-manifest.json').read_text())
assert manifest['commit']=='96ccea6d7fa1adcdb410390a983ae342f3ca1686'
for target in ('fedora','leap','el10'):
 assert json.loads(Path('results/grpc-macro-isolation-20261008',target+'.json').read_text())['exit_code']==0
osc=['osc','--setopt','http_retries=1','-A','https://api.opensuse.org','api'];base='/source/home:davidnichols:qore:testing/qore-grpc-module'
meta=subprocess.check_output([*osc,base+'/_meta']);(out/'metadata-before.xml').write_bytes(meta);m=ET.fromstring(meta)
assert [e.tag for e in m.find('publish')]==['disable']
assert {(e.attrib['repository'],e.attrib['arch']) for e in m.find('build') if e.tag=='enable'}=={(r,a) for r in ['Fedora_44','AlmaLinux_10','openSUSE_Leap_16.0'] for a in ['x86_64','aarch64']}
old=ET.fromstring(subprocess.check_output([*osc,base]));assert old.attrib['srcmd5']=='8a3b51631d9bd3937aca79c8815fbd4f'
with (out/'upload.log').open('x') as log:
 subprocess.run(['python3','-B','-W','error','tools/obs.py','upload','--project','home:davidnichols:qore:testing','--source',str(source),'--apply'],stdout=log,stderr=subprocess.STDOUT,check=True)
listing=subprocess.check_output([*osc,base]);(out/'source.xml').write_bytes(listing);remote=ET.fromstring(listing)
assert {e.attrib['name'] for e in remote.findall('entry')}==set(manifest['sources'])|{'source-manifest.json'}
for e in remote.findall('entry'):assert hashlib.md5((source/e.attrib['name']).read_bytes()).hexdigest()==e.attrib['md5']
after=subprocess.check_output([*osc,base+'/_meta']);(out/'metadata-after.xml').write_bytes(after);assert after==meta
(out/'manifest.json').write_bytes((source/'source-manifest.json').read_bytes())
print(remote.attrib,flush=True)
