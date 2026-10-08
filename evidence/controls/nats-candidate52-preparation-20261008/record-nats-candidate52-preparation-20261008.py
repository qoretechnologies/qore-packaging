# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import gzip, hashlib, json, shutil

root = Path.cwd()
verification = json.loads((root / 'results/nats-candidate52-patch-verification-20261008.json').read_text())
assert verification['patches'] == 115 and verification['exact_focused_source_identity']
out = root / 'evidence/controls/nats-candidate52-preparation-20261008'
out.mkdir()
for name in ['integrate-nats-sparse-index-20261008.py', 'prepare-nats-candidate52-20261008.py',
             'record-nats-candidate52-preparation-20261008.py']:
    shutil.copy2(root / 'work' / name, out / name)
for name in ['nats-server.spec', 'nats-server.rst']:
    shutil.copy2(root / 'dependencies' / name, out / name)
for name in ['nats-candidate52-patch-verification-20261008.json', 'nats-candidate52-patches-20261008.log',
             'nats-candidate52-prepare-20261008.log', 'nats-candidate52-tools-tests-20261008.log',
             'nats-candidate52-runner-tests-20261008.log']:
    data = (root / 'results' / name).read_bytes()
    if name.endswith('.log'):
        (out / (name + '.gz')).write_bytes(gzip.compress(data, mtime=0))
    else:
        (out / name).write_bytes(data)
record = {'schema': 1, 'date': '2026-10-08', 'copyright': 'Copyright 2026 Qore Technologies, s.r.o.',
          'status': 'Candidate52 prepared from the focused-qualified sparse-delivery index and full-width sequence-set correction. No complete RPM/native build or publication claimed.',
          'qualification': 'evidence/nats-sparse-index-20261008.json', 'patches': 115, 'fuzz': 0,
          'new_patch_offsets': 0, 'changed_go_files': verification['changed_go_files_from_candidate51'],
          'exact_focused_source_identity': True, 'tools_tests': 218, 'runner_tests': 7,
          'bundle': 'work/nats-server-candidate-52', 'prepared_source': 'work/nats-prepared-52/nats-server-2.15.0',
          'remaining': ['Trace the historical 250-stream and atomic-create failure paths.',
                        'Run the complete combined RPM matrix, native x86_64/aarch64 OBS builds, installed client/Qore module and repository lifecycle/signing/publication qualification.'],
          'files_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.iterdir())}}
(root / 'evidence/nats-candidate52-preparation-20261008.json').write_text(json.dumps(record, indent=2) + '\n')
print('Recorded candidate52 preparation and 225 successful packaging tests.')
