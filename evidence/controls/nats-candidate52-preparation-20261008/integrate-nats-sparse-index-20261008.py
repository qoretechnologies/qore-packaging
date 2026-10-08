# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib, json, shutil

root = Path.cwd()
e = json.loads((root / 'evidence/nats-sparse-index-20261008.json').read_text())
assert e['qualification']['race_results'] == 948
assert e['qualification']['nonrace_results'] == 27
for name, expected in e['files_sha256'].items():
    assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
name = 'nats-server-memory-subject-sequences.patch'
shutil.copy2(root / 'evidence/controls/nats-sparse-index-20261008' / name, root / 'dependencies' / name)
p = root / 'dependencies/nats-server.spec'
s = p.read_text()
anchor = 'Patch113: nats-server-stream-create-rejection.patch\n'
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + 'Patch114: ' + name + '\n')
anchor = '%changelog\n* Thu Oct 08 2026 David Nichols <david@qore.org> - 2.15.0-1.qore\n'
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + '- Index sparse memory-store subjects for direct filtered delivery.\n- Correct sequence-set upper-bound overflow and cover index lifecycle operations.\n')
p.write_text(s)
p = root / 'dependencies/sources.json'
s = json.loads(p.read_text())
assert name not in s['nats-server']['extra_sources']
s['nats-server']['extra_sources'].append(name)
p.write_text(json.dumps(s, indent=2) + '\n')
p = root / 'dependencies/nats-server.rst'
s = p.read_text().replace('Candidate 51 combines upstream 2.15.0 with 114 patches.',
                         'Candidate 52 combines upstream 2.15.0 with 115 patches.')
s = s.replace('open, together with the historical atomic-create and sparse-performance gates.',
              'open, together with the historical atomic-create gate. Sparse delivery now has\na focused-qualified runtime correction; its combined RPM qualification remains open.')
s += '''
Sparse memory-store delivery
----------------------------

Literal filtered delivery previously scanned every sequence between a subject's
first and last message. Four messages separated by two million unrelated messages
therefore required two million map lookups. Profiles limited to the delivery
benchmark attribute 62–75% of sampled CPU to this scan.

Memory-store subjects now retain a compressed sequence index after first growing
beyond one message. Insertions and removals update it under the existing store
mutex; literal delivery seeks the next matching sequence through the AVL tree.
Existing lazy bounds, external subject-state results and wildcard semantics are
preserved. Purge, reset and final subject deletion release the associated index.
Sequence-set range comparisons also avoid unsigned overflow in the final uint64
block; the original fails the maximum-sequence regression on all three targets.

All 975 focused results pass on Fedora, Leap and AlmaLinux, including 948 under
the race detector. The original sparse workload and 500 ms bound remain in force;
memory delivery measures 61–79 microseconds per operation in these runs. Storage
controls measure allocation increases of approximately 0.08%, 1.3% and 5.5% for
10,000 messages across one, 16 and 10,000 subjects respectively. Their three-sample
medians show no throughput regression, but do not cover every workload or native
architecture. See ``evidence/nats-sparse-index-20261008.json`` for controls, source,
audit, exact measurements and limits. Full combined RPM/native and installed
qualification remains required.
'''
p.write_text(s)
print('Integrated tested Patch114; candidate52 has 115 patches.')
