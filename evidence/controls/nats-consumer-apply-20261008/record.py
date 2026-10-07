# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib
import gzip
import hashlib
import json
import re
import runpy
import shutil
import subprocess

root = Path.cwd()
out = root / 'evidence/controls/nats-consumer-apply-20261008'
out.mkdir()
source = root / 'work/nats-prepared-48/nats-server-2.15.0/server'
fixed = root / 'work/nats-workqueue-inflight-264-20261008'
results = []
for number, count in [(264, 40), (265, 42)]:
 for target in ['fedora', 'leap', 'el10']:
  name = f'{target}-nats-workqueue-inflight-{number}' + ('-broad' if number == 265 else '')
  run = root / 'results' / name
  status = json.loads((run/'status.json').read_text())
  text = (run/'tests.log').read_text()
  assert status['exit_code'] == 0 and '-race' in status['command'], name
  assert len(re.findall(r'^\s*--- PASS:', text, re.M)) == count, name
  assert not re.search(r'WARNING: DATA RACE|--- FAIL:|\[ERR\]|\[WRN\]', text), name
  if number == 265:
   expected = set(status['command'][status['command'].index('-run') + 1][2:-2].split('|'))
   actual = set(re.findall(r'^=== RUN   ([^/\s]+)$', text, re.M))
   assert len(expected) == 25 and expected == actual, (expected-actual, actual-expected)
  results.append({'target': target, 'run': number, 'race_enabled_results_including_subtests': count, 'exit_code': 0})
  shutil.copy2(run/'status.json', out/(name+'-status.json'))
  (out/(name+'.log.gz')).write_bytes(gzip.compress((run/'tests.log').read_bytes(),mtime=0))
controls=[]
for number, variants in [(256,['original','fixed']), (257,['original','fixed']), (263,[''])]:
 for variant in variants:
  for target in ['fedora','leap','el10']:
   name=f'{target}-nats-workqueue-inflight-{number}' + ('-'+variant if variant else '')
   run=root/'results'/name
   status=json.loads((run/'status.json').read_text())
   text=(run/'tests.log').read_text()
   expected=1 if (number==256 and variant=='original') or (number==257 and variant=='fixed') or number==263 else 0
   assert status['exit_code']==expected, name
   if number==256 and variant=='original':
    assert 'context deadline exceeded' in text and 'AddConsumer requests: [$JS.API.CONSUMER.INFO.TEST.test]' in text
   if number==257 and variant=='fixed': assert 'nats: consumer not found' in text
   if number==263:
    assert len(re.findall(r'^    --- FAIL: .*?/shutdown',text,re.M))==5
    assert 'require int equal, but got: 2 != 0' in text
   controls.append({'run':number,'target':target,'variant':variant,'expected_exit_code':expected})
   shutil.copy2(run/'status.json',out/(name+'-status.json'))
   (out/(name+'.log.gz')).write_bytes(gzip.compress((run/'tests.log').read_bytes(),mtime=0))
# Preserve failed setup/qualification iterations rather than treating them as passing tests.
for number in (255,258,260,261,262):
 for run in sorted((root/'results').glob(f'*-nats-workqueue-inflight-{number}*')):
  for name in ['status.json','tests.log']:
   p=run/name
   if p.exists(): (out/(run.name+'-'+name+'.gz')).write_bytes(gzip.compress(p.read_bytes(),mtime=0))
for number in (256,258,259,260,261,262,263,264):
 p=root/f'work/prepare-nats-workqueue-inflight-{number}-20261008.py'
 shutil.copy2(p,out/p.name)
for number in (256,257,263,264,265):
 p=root/f'work/nats-workqueue-inflight-{number}.json'
 shutil.copy2(p,out/p.name)
shutil.copy2(root/'work/run-nats-focused-38.py',out/'run-nats-focused.py')
shutil.copy2(root/'work/nats-workqueue-inflight-256-20261008/nats-server-consumer-info-inflight-delete.patch',out/'withdrawn-immediate-not-found.patch')
for name in ['jetstream_api.go','jetstream_cluster.go','jetstream_cluster_2_test.go']:
 (out/(name+'.gz')).write_bytes(gzip.compress((fixed/name).read_bytes(),mtime=0))
patch='# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.\n'
patch+='# Re-evaluate consumer information after pending metadata deletion has applied.\n'
for name in ['jetstream_api.go','jetstream_cluster.go','jetstream_cluster_2_test.go']:
 patch+=''.join(difflib.unified_diff((source/name).read_text().splitlines(True),(fixed/name).read_text().splitlines(True),fromfile='a/server/'+name,tofile='b/server/'+name))
patch_path=out/'nats-server-consumer-info-apply.patch'
patch_path.write_text(patch)
check=subprocess.run(['patch','--dry-run','--batch','--fuzz=0','-p1','-i',str(patch_path)],cwd=source.parent,capture_output=True,text=True,check=True)
assert not check.stderr and 'offset' not in check.stdout.lower() and 'fuzz' not in check.stdout.lower()
(out/'patch-check.txt').write_text(check.stdout)
audit=runpy.run_path(str(root/'work/write-scoped-audit.py'))
passes={
9:'The patch, qualification scripts and evidence carry 2026 copyright; upstream source headers already include 2026.',
53:'Fixes request loss by joining actual proposal application. No retry timer, timeout relaxation, error suppression or unconditional not-found response is added. The immediate-error proposal is explicitly withdrawn after its upstream regression failed.',
54:'Request bytes and the sole required parser field are copied before asynchronous use. Every completion, term reset, node/cluster/server shutdown and rejected goroutine start releases its counted slot. The tests join owned workers and server shutdown; Go has no manual native allocation ownership here.',
55:'Pending proposal channels and retention counts use js.mu; API counters and limits use atomics. The original consumer leader remains free to respond. All 246 final qualification results pass the Go race detector.',
56:'Typed consumer assignments, channels, parser state and result structs are used. The extended inflight record uses named fields to avoid positional initializer ambiguity.',
57:'Ordinary requests use bounded map lookups. Deferred requests are capped by the configured information-queue limit, with one event-driven waiter per retained request and no polling. Completion returns requests to the existing bounded worker queue. Leadership cleanup is linear in outstanding proposals.',
58:'Tests cover absent assignments, ordinary reads, live consumers on local/remote leaders, queue-cap rejection, incomplete application, term reset, shutdown, rejected starts, copied request data and the real update/delete/recreate path. Overload returns the existing cluster-unavailable API error. Failed experimental harnesses are retained separately.',
59:'Comments and evidence explain applied versus pending state, ownership, resource bounds, cancellation and the historical reproduction limits. The new permanent tests distinguish real replicated operations from synthetic lifetime controls.',
61:'Internal controls run on isolated Docker networks with no published ports or credentials. Request retention is bounded; payloads are copied and released on completion or shutdown. No public API or permission bypass is introduced.',
62:'The original loses all three real information probes after acknowledged deletion. The proposed immediate not-found shortcut fails the existing live-consumer regression on every distribution. The final fix passes 120 focused results plus 126 results from 25 broader named suites per distribution, all with -race. A missing shutdown guard is rejected by 15 exact lifecycle controls.'}
audit['write'](out/'audit.rst','NATS consumer-information metadata-apply audit',
 'Scope: focused-qualified Go implementation, permanent regression tests and their packaging patch. 10 Pass, 52 N/A, 0 Fail. Full RPM, native OBS and installed-package qualification remain required. No C++ implementation changes.',
 passes,'No corresponding Qore module, QPP, DataProvider, C++ implementation, Qore-language test or JAR change.')
shutil.copy2(Path(__file__),out/'record.py')
record={
 'schema':1,'date':'2026-10-08','copyright':'Copyright 2026 Qore Technologies, s.r.o.',
 'status':'Real consumer-info timeout corrected and focused-qualified. Next combined RPM candidate integration and full package qualification remain required.',
 'root_cause':'A remote consumer leader can apply and acknowledge deletion while the metadata leader still has an older applied assignment. AddConsumer first sends ConsumerInfo. The metadata leader discards it in favor of the now-deleted consumer leader, while the other servers have no assignment and also discard it; later application does not recover the request.',
 'fix':'Retain the metadata leader information request until its outstanding consumer proposals finish, then re-evaluate through the ordinary bounded API queue. Preserve immediate reads from a still-live consumer leader. Copy request ownership, cap retention by infoQueueLimit, release on term/node/cluster/server changes and reject replay once shutdown starts.',
 'real_control':'An actual consumer update is held at the metadata leader local consumer mutex, outside the metadata lock. A different consumer leader acknowledges the real update and deletion. All three information callbacks are observed before the local application is released. The old server still times out; the fixed server sends INFO then CREATE, creates a fresh consumer and retains all 40 workqueue messages through five recreate lifetimes.',
 'qualification':{'race_enabled_results_including_subtests':246,'results':results,'broader_named_suites_per_distribution':25,'patch_fuzz_and_offsets':0},
 'controls':controls,
 'withdrawn_proposal':'Returning consumer-not-found merely because a delete is pending breaks TestJetStreamClusterConsumerInfoWithInflightConsumerDelete on every distribution. That proposal is never integrated.',
 'harness_and_proposal_corrections':[
 '255 tried overlaying a new test file into a read-only mount and never executed Go. The regression was moved into an existing test file.',
 '258 used a promoted parser field in a struct literal; 260 shadowed the client type. Both compile errors were corrected before qualification.',
 '261 used a test-only info queue limit of two while replaying two requests, intentionally triggering the existing queue-drain policy. The ordinary capacity is restored after the separate retention-cap assertion.',
 '261/262/263 expected no replay during shutdown, but server shutdown first triggers a Raft term change. The final proposal checks the shutdown state before replay. All retained counters already returned to zero; the failed assertion was the unexpected replay count, not a retained allocation.',
 'WaitForShutdown joins full teardown in the final controls. It alone did not correct the replay failure; that required the production shutdown guard.'
 ],
 'limits':[
 'The candidate36 historical timeout has no per-request trace. The controlled real update/delete sequence demonstrates a reproducible defect in the same public AddConsumer information-probe path, not a trace of the historical scheduler interleaving.',
 'Synthetic proposal entries are used only for the explicitly labeled capacity, ownership and cleanup tests. The root-cause reproduction uses real committed update and delete operations and no fabricated assignments.',
 'Metadata leadership loss releases/re-evaluates retained requests; it does not promise transparent client-operation completion through unavailable consensus or partitions.',
 'Full combined RPM builds, upstream skip review, native architectures, NATS client/module and repository lifecycle remain independent release gates.'
 ],
 'source_sha256':{name:hashlib.sha256((fixed/name).read_bytes()).hexdigest() for name in ['jetstream_api.go','jetstream_cluster.go','jetstream_cluster_2_test.go']},
 'files_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}
}
(root/'evidence/nats-consumer-apply-20261008.json').write_text(json.dumps(record,indent=2)+'\n')
print('Recorded 246 passing race-enabled results, original/withdrawn negative controls and all 62 audit entries')
