# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip,hashlib,json,re,shutil
root=Path.cwd()
out=root/'evidence/controls/nats-candidate50-preparation-20261008'
out.mkdir()
p=root/'results/nats-candidate50-patch-verification-20261008.json'
e=json.loads(p.read_text())
assert e['patches']==113 and e['fuzz']==0 and e['exact_focused_source_identity']
shutil.copy2(p,out/p.name)
for name in ['nats-candidate50-prepare-20261008.log','nats-candidate50-patches-20261008.log','nats-candidate50-tools-tests-20261008.log','nats-candidate50-runner-tests-20261008.log']:
 p=root/'results'/name
 (out/(name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
shutil.copy2(root/'work/prepare-nats-candidate50-20261008.py',out/'prepare.py')
shutil.copy2(root/'dependencies/nats-server.rst',out/'nats-server.rst')
shutil.copy2(root/'dependencies/nats-server.spec',out/'nats-server.spec')
shutil.copy2(Path(__file__),out/'record.py')
record={'schema':1,'date':'2026-10-08','copyright':'Copyright 2026 Qore Technologies, s.r.o.',
 'status':'Candidate50 is prepared with the focused-qualified MQTT pre-restart storage correction and earlier qualified fixes. Full builds have not started; candidate46 is still collecting complete results.',
 'patches':113,'fuzz':0,'new_patch_offsets':0,'exact_focused_source_identity':True,
 'changed_go_files_from_candidate49':e['changed_go_files_from_candidate49'],
 'qualification':{'race_enabled_cases':75,'tool_tests':218,'runner_tests':7,'evidence':'evidence/nats-mqtt-retained-20261008.json'},
 'remaining':['Review all candidate46 results before starting the combined full matrix.','Historical sparse-consumer performance and atomic-batch creation, upstream skip review, native OBS, NATS client/module and repository lifecycle remain release gates.'],
 'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}}
(root/'evidence/nats-candidate50-preparation-20261008.json').write_text(json.dumps(record,indent=2)+'\n')
print('Recorded combined candidate50 source identity and 225 packaging-tool checks')
