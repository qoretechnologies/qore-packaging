# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
from collections import Counter
import gzip,hashlib,json,shutil
root=Path.cwd();out=root/'evidence/controls/nats-candidate46-final-20261008';out.mkdir(exist_ok=True)
statuses=json.loads((root/'results/nats-candidate46-build-status-20261008.json').read_text());assert statuses==dict.fromkeys(('fedora','leap','el10'),1)
results={}
for target in statuses:
 base=root/'results'/f'{target}-nats-server-candidate-46'
 build=json.loads((base/'build.json').read_text());assert build['exit_code']==1
 report=list(base.glob('rpmbuild/BUILD/*/nats-test-results.json'))+list(base.glob('rpmbuild/BUILD/*/*/nats-test-results.json'));assert len(report)==1
 report=report[0];data=json.loads(report.read_text());assert data['exit_code']==1
 raw=(base/'build.log').read_text();events=[]
 for line in raw.splitlines():
  if line.startswith('{"Time":'):
   try:events.append(json.loads(line))
   except json.JSONDecodeError:raise
 terminal=[e for e in events if e.get('Test') and e['Action'] in ('pass','skip','fail')]
 failures=[e for e in terminal if e['Action']=='fail'];failed_names={e['Test'] for e in failures}
 assert len(failures)==1,(target,failures)
 for group in data['groups']:
  assert set(group['selected'])==set(group['terminal']),(target,group['group'])
 assert set(data['packages'])=={g['package'] for g in data['groups']}
 outputs=[e for e in events if e.get('Test') in failed_names]
 for source,name in [(base/'build.json',target+'-build.json'),(report,target+'-tests.json')]:shutil.copy2(source,out/name)
 (out/(target+'-build.log.gz')).write_bytes(gzip.compress(raw.encode(),mtime=0))
 (out/(target+'-failure.json')).write_text(json.dumps(outputs,indent=2)+'\n')
 results[target]={'build_exit_code':1,'all_selected_tests_have_terminal_results':True,'groups':len(data['groups']),'top_level_and_subtest_terminal_counts':dict(Counter(e['Action'] for e in terminal)),'failures':failures,'error':data['error']}
shutil.copy2(root/'work/record-nats-candidate46-final-20261008.py',out/'record.py')
shutil.copy2(root/'work/nats-candidate46-memory-create-triage-20261008.json',out/'memory-create-triage.json')
record={'schema':1,'date':'2026-10-08','copyright':'Copyright 2026 Qore Technologies, s.r.o.','status':'All three full candidate46 runs terminated with one failed test each. Failed builds remain failed; two later qualified corrections and a third unresolved create failure prevent release.','source':'evidence/nats-candidate46-integration-20261008.json','results':results,'qualified_later_fixes':{'fedora':'evidence/nats-extended-interest-20261008.json','el10':'evidence/nats-mqtt-retained-20261008.json'},'remaining':['Root-cause the Leap initial 250-concurrent-stream creation timeout; current trace-only controls do not reproduce it.','Qualify the complete combined candidate50 patch set after resolving the creation failure.','Historical initial atomic-create timeout and sparse-consumer performance gates remain open.','Complete NATS client/module, native OBS, installed-package, repository lifecycle and publication gates.'],'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}}
(root/'evidence/nats-candidate46-final-20261008.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(results,indent=2))
