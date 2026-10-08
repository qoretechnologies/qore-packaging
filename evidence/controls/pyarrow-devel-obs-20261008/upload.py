# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,subprocess,xml.etree.ElementTree as ET
source=Path('work/python-pyarrow-devel-final-20261008');manifest=json.loads((source/'source-manifest.json').read_text());qualified=json.loads(Path('evidence/pyarrow-devel-20261008.json').read_text())
assert manifest['sources']==qualified['source']['sources'];assert not manifest.get('candidate')
for p,h in manifest['sources'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==h,p
for p,h in qualified['files_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
assert qualified['tests']['lint_errors']==qualified['tests']['lint_warnings']==0
out=Path('results/pyarrow-devel-upload-20261008');out.mkdir();osc=['osc','--setopt','http_retries=1','-A','https://api.opensuse.org','api'];base='/source/home:davidnichols:qore:testing/python-pyarrow'
meta=subprocess.check_output([*osc,base+'/_meta']);(out/'metadata-before.xml').write_bytes(meta);assert [e.tag for e in ET.fromstring(meta).find('publish')]==['disable']
old=subprocess.check_output([*osc,base]);(out/'source-before.xml').write_bytes(old);o=ET.fromstring(old);assert o.get('rev')=='1' and o.get('srcmd5')=='e2eb463bb7a1558db46f5755cb56ef55'
with (out/'upload.log').open('x') as log:subprocess.run(['python3','-B','-W','error','tools/obs.py','upload','--project','home:davidnichols:qore:testing','--source',str(source),'--apply'],stdout=log,stderr=subprocess.STDOUT,check=True)
remote=subprocess.check_output([*osc,base]);(out/'source.xml').write_bytes(remote);r=ET.fromstring(remote)
assert {e.get('name'):e.get('md5') for e in r.findall('entry')}=={n:hashlib.md5((source/n).read_bytes()).hexdigest() for n in [*manifest['sources'],'source-manifest.json']}
after=subprocess.check_output([*osc,base+'/_meta']);(out/'metadata-after.xml').write_bytes(after);assert after==meta
(out/'manifest.json').write_bytes((source/'source-manifest.json').read_bytes());print(r.attrib,flush=True)
