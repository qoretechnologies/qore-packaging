# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import gzip,hashlib,json,re,subprocess,xml.etree.ElementTree as ET
root=Path.cwd();base=root/'results/grpc-cmake-native-20261008';out=root/'evidence/controls/grpc-cmake-native-20261008';out.mkdir()
state=ET.parse(base/'final-state.xml');osc=['osc','--setopt','http_retries=1','-A','https://api.opensuse.org','api']
def record(pair):
 repo,arch=pair;name=repo+'-'+arch;d=base/name;b=ET.parse(d/'buildinfo.xml');assert b.findtext('rev')=='3' and b.findtext('srcmd5')=='8a3b51631d9bd3937aca79c8815fbd4f'
 rows=[r for r in state.findall('result') if r.get('repository')==repo and r.get('arch')==arch];assert len(rows)==1 and rows[0].find('status').get('code')=='succeeded'
 history=subprocess.check_output([*osc,f'/build/home:davidnichols:qore:testing/{repo}/{arch}/qore-grpc-module/_history'])
 assert any(e.get('srcmd5')==b.findtext('srcmd5') and e.get('rev')=='3' for e in ET.fromstring(history)),history
 raw=(d/'build.log').read_bytes();text=raw.decode();assert "srcmd5 '8a3b51631d9bd3937aca79c8815fbd4f'" in text
 counts=re.findall(r'Ran (\d+) test cases, (\d+) succeeded \((\d+) assertions\)',text)
 assert len(counts)==13 and list(map(sum,zip(*(map(int,c) for c in counts))))==[378,378,1768]
 assert 'Ran 6 tests in' in text and 'Ran 3 tests in' in text
 assert not re.search(r'CMake (Warning|Error)|: warning:|: E:|: W:',text)
 dest=out/name;dest.mkdir();(dest/'build.log.gz').write_bytes(gzip.compress(raw,mtime=0));(dest/'buildinfo.xml').write_bytes((d/'buildinfo.xml').read_bytes());(dest/'history.xml').write_bytes(history)
 return name,{'status':'succeeded','revision':3,'srcmd5':b.findtext('srcmd5'),'suites':13,'cases':378,'assertions':1768,'uninstall_tests':6,'dependency_parser_tests':3,'compiler_or_cmake_warnings':0}
with ThreadPoolExecutor(max_workers=4) as pool:records=dict(pool.map(record,[(r,a) for r in ['Fedora_44','AlmaLinux_10'] for a in ['x86_64','aarch64']]))
(out/'state.xml').write_bytes((base/'final-state.xml').read_bytes());(out/'record.py').write_bytes(Path(__file__).read_bytes())
e={'schema':1,'date':'2026-10-08','copyright':'Copyright 2026 Qore Technologies, s.r.o.','status':'Four corrected native builds pass with no CMake or compiler warnings. Leap dependency and installed checks remain.','module_commit':'5f6cc3469e82f98c78c00e32f07d34c41a03a0c5','records':records,'retained_diagnostics':'Fedora/AlmaLinux grpc_tools deprecation is covered by evidence/grpc-tools-diagnostic-20261002.json; previously recorded OBS bootstrap diagnostics remain outside package tests.','history_timing':'Early per-log history snapshots could precede OBS recording the terminal build; refreshed history after the final succeeded result confirms revision3 for all four builds.','remaining':'PyArrow completion to unblock Leap, signed installed ARM tests, develop integration and final current-core repository lifecycle gates.','files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()}}
(root/'evidence/grpc-cmake-native-20261008.json').write_text(json.dumps(e,indent=2)+'\n');print(records,flush=True)
