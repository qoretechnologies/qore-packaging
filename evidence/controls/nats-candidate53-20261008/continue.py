# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Join the live candidate53 driver, validate its full result, then build candidate55."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import collections
import gzip
import hashlib
import json
import os
import re
import select
import subprocess

root=Path.cwd()
old_status=root/'results/nats-candidate53-build-status-20261008.json'
out=root/'results/nats-candidate55-handoff-20261008'
out.mkdir()
pid=2474796
if not old_status.exists():
    fd=os.pidfd_open(pid)
    try:
        command=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        assert b'work/build-nats-candidate53-20261008.py' in command,command
        (out/'joined-driver.json').write_text(json.dumps({'pid':pid,'command':[s.decode() for s in command if s],
            'mechanism':'pidfd readiness; no timer, sleep or repeated status polling'},indent=2)+'\n')
        print('Joined live candidate53 driver through pidfd; no new build starts before its verified terminal result.',flush=True)
        select.select([fd],[],[])
    finally:
        os.close(fd)
assert old_status.exists(),'Candidate53 driver ended without its terminal result; inspect it before any new build.'
summary=json.loads(old_status.read_text())
records={}
expected={'fedora':{'TestJetStreamConsumerMultipleFiltersLastPerSubject','TestNRGLeaderResurrectsRemovedPeers'},
          'leap':set(),'el10':set()}
problems=[]
for target in expected:
    base=root/f'results/{target}-nats-server-candidate-53'
    manifest=json.loads((base/'build.json').read_text())
    log=(base/'build.log').read_text()
    events=[json.loads(line) for line in log.splitlines() if line.startswith('{"Time"')]
    counts=collections.Counter(e['Action'] for e in events if e.get('Test') and e['Action'] in ['pass','fail','skip'])
    failed=[e for e in events if e.get('Test') and e['Action']=='fail']
    failures={e['Test'] for e in failed}
    packages={e['Package'] for e in events if e.get('Action') in ['pass','fail'] and not e.get('Test')}
    assert 'github.com/nats-io/nats-server/v2/test' in packages, 'Final integration package did not finish'
    assert 'github.com/nats-io/nats-server/v2/server' in packages
    traces=[{'package':row['Package'],'test':row['Test'],
        'output':''.join(e.get('Output','') for e in events if e.get('Test')==row['Test'] and e['Package']==row['Package'])} for row in failed]
    records[target]={'build_exit_code':manifest['exit_code'],'terminal_results':dict(counts),'failures':traces,
                     'artifacts':manifest.get('artifacts',{})}
    for name in ['build.json','build.log']:
        data=(base/name).read_bytes()
        (out/(target+'-'+name+('.gz' if name.endswith('.log') else ''))).write_bytes(gzip.compress(data,mtime=0) if name.endswith('.log') else data)
    wanted=1 if expected[target] else 0
    if failures!=expected[target] or manifest['exit_code']!=wanted or summary[target]!=wanted:
        problems.append({'target':target,'actual_failures':sorted(failures),'expected_failures':sorted(expected[target]),
                         'manifest_exit':manifest['exit_code'],'driver_exit':summary[target]})
(out/'candidate53-review.json').write_text(json.dumps({'results':records,'unexpected':problems},indent=2)+'\n')
assert not problems, 'Additional candidate53 failures require diagnosis; candidate55 was not launched.'
verified=json.loads((root/'results/nats-candidate55-patch-verification-20261008.json').read_text())
assert verified['patches']==118 and verified['fuzz']==0 and verified['exact_focused_source_identity']
for name,sha in verified['source_manifest']['sources'].items():
    assert hashlib.sha256((root/'work/nats-server-candidate-55'/name).read_bytes()).hexdigest()==sha,name
for name,count in [('tools',223),('runner',7)]:
    text=(root/f'results/nats-candidate55-{name}-tests-20261008.log').read_text()
    assert re.search(r'Ran '+str(count)+r' tests in [\d.]+s\n\nOK\s*$',text)
for evidence in ['nats-multiple-filter-interest-20261008','nats-peer-commit-20261008']:
    record=json.loads((root/'evidence'/(evidence+'.json')).read_text())
    for rel,sha in record['files_sha256'].items():
        assert hashlib.sha256((root/rel).read_bytes()).hexdigest()==sha,rel
images={
    'fedora':'sha256:f1f889474f303ffe6f98b381e3061e812daa34e9018a00c4a25cb65f9a82fee9',
    'leap':'sha256:2b44d9f9636b4e454c93b06c95cd9ff9f23136b159e80ac2ded68b32d7f1190b',
    'el10':'sha256:0bc68ce99e4cd1340c79149a0601d7496351acd655a537ddae23116f036370c5'
}
def build(target):
    command=['python3','-B','-W','error','tools/build-local.py','--source','work/nats-server-candidate-55',
             '--image',images[target],'--output',f'results/{target}-nats-server-candidate-55',
             '--jobs','2','--internal-interface','--tmpfs-mib','4096']
    with (root/f'results/{target}-nats-candidate55-driver-20261008.log').open('x') as log:
        result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
    return target,result.returncode
print('Candidate53 complete with exactly the two corrected failures; starting all three candidate55 RPM builds.',flush=True)
(out/'candidate55-started.json').write_text(json.dumps({'source':'work/nats-server-candidate-55',
    'targets':images,'prerequisites':'Full prior results inspected; both observed failures have focused fixes; all source hashes verified.'},indent=2)+'\n')
with ThreadPoolExecutor(max_workers=3) as pool:
    results=dict(pool.map(build,images))
(root/'results/nats-candidate55-build-status-20261008.json').write_text(json.dumps(results,indent=2)+'\n')
print(results,flush=True)
raise SystemExit(any(results.values()))
