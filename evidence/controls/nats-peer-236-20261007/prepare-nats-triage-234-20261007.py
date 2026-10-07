# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import subprocess

source = Path('work/nats-prepared-44/nats-server-2.15.0')
output = Path('work/nats-triage-234-20261007')
output.mkdir()

def function(text, name, transform):
    start = text.index('func ' + name + '(')
    end = text.find('\nfunc ', start + 1)
    if end < 0:
        end = len(text)
    return text[:start] + transform(text[start:end]) + text[end:]

def purge(text):
    old = '\t\t\tnc.Request(fmt.Sprintf(JSApiStreamCreateT, cfg.Name), req, time.Second)'
    assert text.count(old) == 1
    text = text.replace(old, '''			createReply, err := nc.Request(fmt.Sprintf(JSApiStreamCreateT, cfg.Name), req, time.Second)
			require_NoError(t, err)
			var created JSApiStreamCreateResponse
			require_NoError(t, json.Unmarshal(createReply.Data, &created))
			if created.Error != nil {
				t.Fatalf("create response: %s", createReply.Data)
			}''')
    old = '\t\t\t_, err = nc.Request(fmt.Sprintf(JSApiStreamPurgeT, "KV"), jr, time.Second)'
    assert text.count(old) == 1
    text = text.replace(old, '\t\t\tpurgeReply, err := nc.Request(fmt.Sprintf(JSApiStreamPurgeT, "KV"), jr, time.Second)')
    marker = '\t\t\t// 18 should still be there'
    assert text.count(marker) == 1
    text = text.replace(marker, '''			t.Logf("purge response: %s", purgeReply.Data)
			var purged JSApiStreamPurgeResponse
			require_NoError(t, json.Unmarshal(purgeReply.Data, &purged))
			if purged.Error != nil {
				t.Fatalf("purge error: %s", purgeReply.Data)
			}
''' + marker)
    return text

def peer(text):
    marker = '\t// Client based API'
    assert text.count(marker) == 1
    return text.replace(marker, '''	// Observe the actual startup state without modifying production timing.
	meta := c.leader().getJetStream().getMetaGroup().(*raft)
	meta.RLock()
	t.Logf("startup: pending=%+v commit=%d applied=%d proposed=%d", meta.membChange, meta.commit, meta.applied, meta.pindex)
	meta.RUnlock()
''' + marker)

files = {}
for filename, name, transform in [
    ('jetstream_cluster_2_test.go', 'TestJetStreamClusterPurgeBySequence', purge),
    ('jetstream_cluster_1_test.go', 'TestJetStreamClusterPeerRemovalAPI', peer),
]:
    text = (source / 'server' / filename).read_text()
    target = output / filename
    target.write_text(function(text, name, transform))
    subprocess.run(['gofmt', '-w', str(target)], check=True)
    files[str(target)] = 'server/' + filename

cases = []
for target in ['fedora', 'leap', 'el10']:
    cases.append({
        'name': target + '-nats-triage-234', 'target': target,
        'count': 60, 'race': True,
        'pattern': '^(TestJetStreamClusterPeerRemovalAPI|TestJetStreamClusterPurgeBySequence)$',
        'sublist': str(source / 'server/sublist.go'), 'overlays': files,
    })
Path('work/nats-triage-234.json').write_text(json.dumps({'source': str(source), 'workers': 3, 'cases': cases}, indent=2) + '\n')
