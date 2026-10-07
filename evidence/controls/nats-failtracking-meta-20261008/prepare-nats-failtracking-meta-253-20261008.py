# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import subprocess

root = Path.cwd()
previous = root / 'work/nats-failtracking-meta-251-20261008'
out = root / 'work/nats-failtracking-meta-253-20261008'
out.mkdir()
for name in ['jetstream_cluster.go', 'jetstream_api.go']:
    (out / name).write_bytes((previous / name).read_bytes())
test = (previous / 'jetstream_cluster_3_test.go').read_text()
needle = '''				select {
				case server := <-gate.requests:
					t.Fatalf("barrier allowed update before metadata readiness on %s", server.Name())
				default:
				}
'''
assert test.count(needle) == 1
test = test.replace(needle, '', 1)
needle = '\t\t\t\tcase <-observed.awaiting:\n'
assert test.count(needle) == 1
test = test.replace(needle, needle + '''					// Check only while API publication is held. After publication,
					// ordinary followers correctly decline the broadcast request.
					select {
					case server := <-gate.requests:
						t.Fatalf("barrier sent update while metadata was paused on %s", server.Name())
					default:
					}
''')
(out / 'jetstream_cluster_3_test.go').write_text(test)
subprocess.run(['gofmt', '-w', str(out / 'jetstream_cluster_3_test.go')], check=True)
config = json.loads((root / 'work/nats-failtracking-meta-251.json').read_text())
for case in config['cases']:
    case['name'] = case['name'].replace('-251', '-253')
    case['overlays'] = {str(p.relative_to(root)): 'server/' + p.name for p in out.iterdir()}
(root / 'work/nats-failtracking-meta-253.json').write_text(json.dumps(config, indent=2) + '\n')
print('Corrected diagnostic assertion to observe premature requests before publication, allowing normal follower returns afterward')
