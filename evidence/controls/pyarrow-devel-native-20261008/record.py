# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import gzip,hashlib,json,re,subprocess,xml.etree.ElementTree as ET
root=Path.cwd();base=root/'results/pyarrow-devel-native-20261008';out=root/'evidence/controls/pyarrow-devel-native-20261008';out.mkdir()
state=ET.parse(base/'final-signed-state.xml');osc=['osc','--setopt','http_retries=1','-A','https://api.opensuse.org','api'];source='01a5a921daefbd1d6a8c88a711b6f098'
def norm(s):
 s=re.sub(r'^\[\s*\d+s\]\s*','',s).strip()
 s=re.sub(r'/(?:work|home/abuild)/rpmbuild/BUILD/[^ ]*?/apache-arrow-25.0.1/','<source>/',s)
 return re.sub(r'/tmp/[^/]+/build/','<generated>/',s)
old=Counter(map(norm,json.loads((root/'evidence/pyarrow-external-diagnostics-20261003.json').read_text())['warning_inventory']))
def record(arch):
 d=base/arch;dest=out/arch;dest.mkdir();b=ET.parse(d/'buildinfo.xml');assert b.findtext('rev')=='2' and b.findtext('srcmd5')==source
 row=[r for r in state.findall('result') if r.get('repository')=='openSUSE_Leap_16.0' and r.get('arch')==arch];assert len(row)==1 and row[0].find('status').get('code')=='succeeded'
 path=f'/build/home:davidnichols:qore:testing/openSUSE_Leap_16.0/{arch}/python-pyarrow'
 for item in ('_history',''):
  data=subprocess.check_output([*osc,path+('/'+item if item else '')]);(dest/('history.xml' if item else 'binaries.xml')).write_bytes(data)
  if item:assert any(e.get('srcmd5')==source and e.get('rev')=='2' for e in ET.fromstring(data))
 raw=(d/'build.log').read_bytes();text=raw.decode();assert source in text and '6616 passed, 1646 skipped, 13 xfailed, 1 xpassed' in text
 assert '3 passed' in text and '0 errors, 0 warnings, 47 filtered, 0 badness' in text
 new=Counter(norm(l) for l in text.splitlines() if ': warning:' in l);assert new==old,(arch,new-old,old-new);assert sum(new.values())==24
 (dest/'build.log.gz').write_bytes(gzip.compress(raw,mtime=0));(dest/'buildinfo.xml').write_bytes((d/'buildinfo.xml').read_bytes())
 (dest/'warnings.json').write_text(json.dumps(dict(new),indent=2)+'\n')
 return arch,{'revision':2,'srcmd5':source,'status':'succeeded','api_tests':3,'upstream_passed':6616,'optional_skips':1646,'expected_failures':13,'nonstrict_unexpected_passes':1,'lint_errors':0,'lint_warnings':0,'approved_compiler_diagnostics':24}
with ThreadPoolExecutor(max_workers=2) as pool:records=dict(pool.map(record,['x86_64','aarch64']))
(out/'state.xml').write_bytes((base/'final-signed-state.xml').read_bytes());(out/'record.py').write_bytes(Path(__file__).read_bytes())
e={'schema':1,'date':'2026-10-08','copyright':'Copyright 2026 Qore Technologies, s.r.o.','status':'Both native builds pass full tests and package lint; development split delivered successfully.','source_commit':'08f280171d7a24e04989a5e7b54c96ac3d779082','records':records,'retained_diagnostics':'Only the exact24 compiler deprecations approved in pyarrow-external-diagnostics-20261003.json. OBS polkit bootstrap diagnostic separately approved; no new filters or flags.','remaining':'Signed installed gRPC/Flight ARM qualification and final repository lifecycle gates.','files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}}
(root/'evidence/pyarrow-devel-native-20261008.json').write_text(json.dumps(e,indent=2)+'\n');print(records)
