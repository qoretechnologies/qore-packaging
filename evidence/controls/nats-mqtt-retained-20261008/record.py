# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib,gzip,hashlib,json,re,runpy,shutil,subprocess
root=Path.cwd()
out=root/'evidence/controls/nats-mqtt-retained-20261008'
out.mkdir(exist_ok=True)
source=root/'work/nats-prepared-49/nats-server-2.15.0/server/mqtt_test.go'
candidates=list((root/'results/el10-nats-server-candidate-46/rpmbuild/BUILD').glob('**/server/mqtt_test.go'))
assert len(candidates)==1
failed_source=candidates[0]
assert source.read_bytes()==failed_source.read_bytes()
assert source.read_text().splitlines()[9391].strip()=='testMQTTCheckPubMsg(t, mc, r, "foo/ok", mqttPubFlagRetain, []byte("ok"))'
results=[]
for number,variant,count in [(266,'clean',20),(267,'control',5)]:
 for target in ['fedora','leap','el10']:
  name=f'{target}-nats-mqtt-retained-{number}-{variant}'
  run=root/'results'/name
  status=json.loads((run/'status.json').read_text());text=(run/'tests.log').read_text()
  assert status['exit_code']==0 and '-race' in status['command']
  assert len(re.findall(r'^--- PASS:',text,re.M))==count
  assert not re.search(r'WARNING: DATA RACE|--- FAIL:|\[ERR\]|\[WRN\]',text)
  if variant=='control': assert text.count('QoS0 write, publisher close and independent legacy PubAck all completed while the valid retained message was still absent')==count
  shutil.copy2(run/'status.json',out/(name+'-status.json'))
  (out/(name+'.log.gz')).write_bytes(gzip.compress((run/'tests.log').read_bytes(),mtime=0))
  results.append({'target':target,'variant':variant,'race_enabled_cases':count,'exit_code':0})
# Retain the control's initially incorrect decoding expectation. MQTT's current
# on-disk representation is the raw payload; the injected legacy record is JSON.
for target in ['fedora','leap','el10']:
 run=root/'results'/f'{target}-nats-mqtt-retained-266-control'
 status=json.loads((run/'status.json').read_text())
 assert status['exit_code']==1
 (out/(run.name+'.log.gz')).write_bytes(gzip.compress((run/'tests.log').read_bytes(),mtime=0))
 shutil.copy2(run/'status.json',out/(run.name+'-status.json'))
entries=[]
with (root/'results/el10-nats-server-candidate-46/build.log').open() as log:
 for line in log:
  if line.startswith('{'):
   try: e=json.loads(line)
   except ValueError: continue
   if e.get('Test')=='TestMQTTRetainedMessageWithDelSubjectIsNotRestored': entries.append(e)
assert any(e.get('Action')=='fail' for e in entries)
(out/'candidate46-failure.json').write_text(json.dumps(entries,indent=2)+'\n')
clean=root/'work/nats-mqtt-retained-266-20261008/clean.go'
control=root/'work/nats-mqtt-retained-267-20261008/control.go'
for name,p in [('clean.go',clean),('control.go',control)]: (out/(name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
patch='# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n# Complete valid retained-message storage before restarting the DEL-recovery fixture.\n'
patch+=''.join(difflib.unified_diff(source.read_text().splitlines(True),clean.read_text().splitlines(True),fromfile='a/server/mqtt_test.go',tofile='b/server/mqtt_test.go'))
patch_path=out/'nats-server-mqtt-restart-storage-tests.patch'
patch_path.write_text(patch)
check=subprocess.run(['patch','--dry-run','--batch','--fuzz=0','-p1','-i',str(patch_path)],cwd=source.parent.parent,capture_output=True,text=True,check=True)
assert not check.stderr and 'offset' not in check.stdout.lower()
(out/'patch-check.txt').write_text(check.stdout)
for name in ['work/prepare-nats-mqtt-retained-266-20261008.py','work/prepare-nats-mqtt-retained-267-20261008.py','work/nats-mqtt-retained-266.json','work/nats-mqtt-retained-267.json','work/run-nats-focused-38.py']:
 shutil.copy2(root/name,out/Path(name).name)
audit=runpy.run_path(str(root/'work/write-scoped-audit.py'))
passes={
9:'The patch and evidence carry 2026 copyright; the upstream test file already ends its copyright range in 2026.',
53:'The restart fixture observes actual retained storage before shutting the server down. No sleep, retry, request-deadline change, runtime change or warning suppression is added.',
54:'The existing retained observer owns its notification state through the test/server lifetime. The diagnostic control releases the held publisher mutex via sync.Once and deferred cleanup, including failure paths.',
55:'The observer uses synchronized state and event notifications. The control holds the real MQTT publisher mutex while an independent NATS publication completes. All 75 final runs pass the Go race detector.',
56:'The fixture uses the existing typed MQTT connection/session helpers. The control checks the exact nats.ErrMsgNotFound result and the stored raw payload, distinct from the legacy JSON input.',
57:'One fixture observer joins a real completion event. There is no production cost, busy waiting or additional benchmark workload.',
58:'Controls prove the valid retained message is absent even after all original pre-restart operations complete; they then verify exact storage, restart delivery and rejection of the invalid DEL record. Every error is checked.',
59:'The source comment and evidence explain why QoS0 transport writes and independent PubAck cannot establish retained storage; the control model and earlier recovery bug are distinguished.',
61:'The experiments use isolated Docker networks and the existing local fixture credentials. No runtime protocol, authentication, configuration or published port changes are made.',
62:'60 clean runs and 15 controlled ordering runs pass across three distributions. The failed package source is byte-identical to the tested baseline. The package diff only adds a stable publisher identifier and the existing retained-completion join.'}
audit['write'](out/'audit.rst','NATS MQTT restart storage-precondition audit','Scope: focused-qualified test fixture and diagnostic control. 10 Pass, 52 N/A, 0 Fail. Full combined package qualification remains required. No runtime or C++ implementation change.',passes,'No corresponding Qore module, QPP, DataProvider, C++ implementation, Qore-language test or JAR change.')
shutil.copy2(Path(__file__),out/'record.py')
record={'schema':1,'date':'2026-10-08','copyright':'Copyright 2026 Qore Technologies, s.r.o.',
 'status':'The candidate46 MQTT restart fixture storage precondition is corrected and focused-qualified; combined package integration remains required.',
 'failure':'AlmaLinux candidate46 times out at mqtt_test.go:9392 waiting for the valid retained foo/ok message after restart.',
 'root_cause':'The fixture writes QoS0 and closes its MQTT socket, then receives PubAck for a different record on a NATS socket. Those operations do not guarantee the valid MQTT publication has been read or stored before server shutdown. Earlier retained-index replay readiness cannot recover a record absent from storage.',
 'fix':'Give the publisher a stable test ID, observe its actual retained callback and join the valid payload before closing it and restarting. All original retained-message, invalid-DEL, QoS and request-deadline assertions remain unchanged.',
 'qualification':{'race_enabled_cases':75,'results':results,'patch_fuzz_and_offsets':0},
 'control':'Hold the real server-side MQTT publisher mutex while the original QoS0 write, TCP close and independent legacy-message PubAck complete. A real JetStream GetLastMsg still reports the valid subject absent. Release that read path, join retained completion, verify its exact stored raw payload, then complete the original restart and invalid-DEL assertions.',
 'harness_correction':'The first control incorrectly tried JSON decoding the current raw-payload MQTT record. The deliberately injected legacy invalid record uses JSON; current MQTT storage does not. The final control checks the correct raw representation; the clean patch is unchanged.',
 'prior_related_evidence':['evidence/nats-mqtt-readiness-20261003.json','evidence/nats-retained-completion-20261004.json'],
 'limits':['The mutex control deterministically disproves the fixture precondition and then completes recovery; it does not trace the historical scheduler or force the original ten-second timeout.','The prior runtime retained-replay readiness correction remains necessary and unchanged. The new join verifies pre-shutdown storage, not merely producer PING completion.','Only the clean fixture changes enter the package. Mutex manipulation and additional NATS probes are confined to the control.','Full combined RPM and native/installed qualification remain required.'],
 'source_sha256':{'baseline':hashlib.sha256(source.read_bytes()).hexdigest(),'clean':hashlib.sha256(clean.read_bytes()).hexdigest()},
 'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}}
(root/'evidence/nats-mqtt-retained-20261008.json').write_text(json.dumps(record,indent=2)+'\n')
print('Recorded 75 passing MQTT runs, exact package failure and pre-shutdown storage control')
