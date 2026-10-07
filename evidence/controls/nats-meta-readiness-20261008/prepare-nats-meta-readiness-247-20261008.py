# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import subprocess

root = Path.cwd()
previous = root / 'work/nats-meta-readiness-245-20261008'
out = root / 'work/nats-meta-readiness-247-20261008'
out.mkdir()
for name in ['jetstream_cluster.go', 'jetstream_api.go']:
    (out / name).write_bytes((previous / name).read_bytes())
source = (root / 'work/nats-prepared-45/nats-server-2.15.0/server/jetstream_cluster_2_test.go').read_text()
begin = source.index('func TestJetStreamClusterDeleteAndRestoreAndRestart(')
end = source.index('\t// Now restart.', begin)
setup = source[begin:end]
setup = setup.replace('TestJetStreamClusterDeleteAndRestoreAndRestart', 'TestPackagingMetaReadinessAfterRestart')
needle = '\tc := createJetStreamClusterExplicit(t, "JSC", 3)\n'
assert setup.count(needle) == 1
setup = setup.replace(needle, '''	c := createJetStreamClusterWithTemplateAndModHook(t, jsClusterTempl, "META-RESTART", 3,
		func(sn, cn, storeDir, conf string) string {
			return conf + fmt.Sprintf("\\nserver_tags: [%q]\\n", sn)
		})
''')
setup = setup.replace('\tdefer c.shutdown()\n', '''	defer c.shutdown()
	chosenMeta := c.leader()
	require_NotNil(t, chosenMeta)
''')
assert setup.count('nats.StreamConfig{Name: "TEST"}') == 2
setup = setup.replace('nats.StreamConfig{Name: "TEST"}',
                      'nats.StreamConfig{Name: "TEST", Placement: &nats.Placement{Tags: []string{chosenMeta.Name()}}}')
setup = setup.replace('\t\tm.AckSync()\n', '\t\trequire_NoError(t, m.AckSync())\n')
text = (previous / 'jetstream_cluster_2_test.go').read_text()
a = text.index('func TestPackagingMetaReadinessAfterRestart(')
b = text.index('\tawaitClusterMetaApplied(t, c)', a)
text = text[:a] + setup + text[b:]
a = text.index('func TestPackagingMetaReadinessAfterRestart(')
b = text.index('// Observe a real blocking Context', a)
body = text[a:b]
body = body.replace('\toldLeader := c.leader()\n', '''	oldLeader := c.streamLeader(globalAccountName, "TEST")
	require_True(t, oldLeader == chosenMeta)
	require_True(t, c.leader() == oldLeader)
	t.Logf("restarting the same stream/consumer/metadata leader: %s", oldLeader.Name())
''')
assert body.count('info.State.Msgs, uint64(1)') == 1
body = body.replace('info.State.Msgs, uint64(1)', 'info.State.Msgs, uint64(22)')
body = body.replace('''	_, err = js.ConsumerInfo("TEST", "dlc")
	require_NoError(t, err)
''', '''	consumer, err := js.ConsumerInfo("TEST", "dlc")
	require_NoError(t, err)
	require_Equal(t, consumer.AckFloor.Consumer, uint64(5))
''')
text = text[:a] + body + text[b:]
path = out / 'jetstream_cluster_2_test.go'
path.write_text(text)
subprocess.run(['gofmt', '-w', str(path)], check=True)
config = json.loads((root / 'work/nats-meta-readiness-245.json').read_text())
for case in config['cases']:
    case['name'] = case['name'].replace('-245', '-247')
    case['pattern'] = '^TestPackagingMetaReadinessAfterRestart$'
    case['overlays'] = {str(p.relative_to(root)): 'server/' + p.name for p in out.iterdir()}
(root / 'work/nats-meta-readiness-247.json').write_text(json.dumps(config, indent=2) + '\n')
print('Prepared exact delete/recreate/ack history with stream and metadata leadership placed on the restarted server')
