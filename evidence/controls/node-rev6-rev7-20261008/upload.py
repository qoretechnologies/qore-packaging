# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import collections,gzip,hashlib,json,re,subprocess,xml.etree.ElementTree as ET
root=Path.cwd();out=root/'evidence/controls/node-rev6-rev7-20261008';out.mkdir()
project='home:davidnichols:qore:testing';package='nodejs24-libnode';osc=['osc','--setopt','http_retries=1','-A','https://api.opensuse.org','api']
base=f'/source/{project}/{package}'
def get(path,name):
 data=subprocess.check_output([*osc,path]);(out/name).write_bytes(data);return ET.fromstring(data)
oldroot=root/'work/nodejs24-libnode-arm-fixes-20261008';old=json.loads((oldroot/'source-manifest.json').read_text())
listing=get(base,'old-source.xml');assert listing.get('rev')=='6' and listing.get('srcmd5')=='446c131b67f27e8cdbeae0887574f61f'
assert {e.get('name'):e.get('md5') for e in listing.findall('entry')}=={n:hashlib.md5((oldroot/n).read_bytes()).hexdigest() for n in [*old['sources'],'source-manifest.json']}
state=get(f'/build/{project}/_result?package={package}','rev6-state.xml')
records=json.loads((root/'results/node-native-rev6-comparison-20261008.json').read_text())
for arch in ('x86_64','aarch64'):
 rows=[r for r in state.findall('result') if r.get('repository')=='openSUSE_Leap_16.0' and r.get('arch')==arch];assert len(rows)==1 and rows[0].find('status').get('code')=='succeeded'
 raw=(root/f'results/node-native-rev6-live-20261008/{arch}.log').read_bytes();text=re.sub(r'^\[\s*\d+s\] ?','',raw.decode(),flags=re.M)
 assert f"arch '{arch}' srcmd5 '446c131b67f27e8cdbeae0887574f61f'" in raw.decode()
 assert '0 errors, 0 warnings, 15 filtered, 0 badness' in text
 tests=re.findall(r'^(?:not )?ok (\d+) (.+)$',text,re.M);n=5249 if arch=='x86_64' else 5245
 assert len(tests)==n and [int(i) for i,_ in tests]==list(range(1,n+1))
 assert not records[arch]['failed'] and records[arch]['native192'] and not records[arch]['new']
 (out/(arch+'-rev6.log.gz')).write_bytes(gzip.compress(raw,mtime=0))
 (out/(arch+'-rev6-buildinfo.xml')).write_bytes((root/f'results/node-native-rev6-live-20261008/{arch}-buildinfo.xml').read_bytes())
source=root/'work/nodejs24-libnode-arm-initialization-20261008';manifest=json.loads((source/'source-manifest.json').read_text());assert manifest['commit']=='0997787ef8c0c8564640b9faa7bea71166ec206e';assert not manifest.get('candidate')
for p,d in manifest['sources'].items():assert hashlib.sha256((source/p).read_bytes()).hexdigest()==d,p
qualification=json.loads((root/'evidence/node-arm-initialization-fix-20261008.json').read_text())
for p,d in qualification['files_sha256'].items():assert hashlib.sha256((root/p).read_bytes()).hexdigest()==d,p
subprocess.run(['git','merge-base','--is-ancestor',manifest['commit'],'HEAD'],check=True)
subprocess.run(['git','diff','--exit-code',manifest['commit'],'HEAD','--','dependencies/nodejs24*'],check=True)
changed=sorted(p for p,d in manifest['sources'].items() if old['sources'].get(p)!=d)
assert set(old['sources'])<=set(manifest['sources'])
meta=get(base+'/_meta','metadata-before.xml');assert [x.tag for x in meta.find('publish')]==['disable']
with (out/'upload.log').open('x') as log:
 subprocess.run(['python3','-B','-W','error','tools/obs.py','upload','--project',project,'--source',str(source),'--apply'],stdout=log,stderr=subprocess.STDOUT,check=True)
new=get(base,'new-source.xml')
assert {e.get('name'):e.get('md5') for e in new.findall('entry')}=={n:hashlib.md5((source/n).read_bytes()).hexdigest() for n in [*manifest['sources'],'source-manifest.json']}
after=get(base+'/_meta','metadata-after.xml');assert ET.tostring(after)==ET.tostring(meta)
(out/'source-manifest.json').write_bytes((source/'source-manifest.json').read_bytes());(out/'upload.py').write_bytes(Path(__file__).read_bytes())
e={'schema':1,'date':'2026-10-08','copyright':'Copyright 2026 Qore Technologies, s.r.o.','status':'Revision6 full native tests and lint pass on both architectures. Prepared constructor fix uploaded as revision7 for native verification; publication disabled.','revision6':{'srcmd5':'446c131b67f27e8cdbeae0887574f61f','architectures':records},'warning_review':'No new unique compiler diagnostics versus revision5. The two corrected ARM declaration diagnostics disappear. Eight constructor diagnostics remain in rev6 and are addressed by rev7; pio2/BTI and VM experimental-notice decisions remain pending. Exact ARM root-load diagnostic approved.','revision7':dict(new.attrib),'source_commit':manifest['commit'],'source_files_verified':len(manifest['sources'])+1,'changed_sources':changed,'qualification':'evidence/node-arm-initialization-fix-20261008.json','limits':['JavaScript totals include 81 x86_64 and 80 ARM upstream skips; 192 native tests pass on each.','Matching diagnostic text is not a blanket approval for every ARM code path.','Revision7 native and installed module checks remain required before publication.'],'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}}
(root/'evidence/node-rev6-rev7-20261008.json').write_text(json.dumps(e,indent=2)+'\n');print(new.attrib,flush=True)
