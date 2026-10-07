# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
for variant in ['late','early','update','integration']:
 path=Path('work/nats-expiration-229-final-'+variant+'.json')
 with Path('results/nats-expiration-229-final-'+variant+'-driver.log').open('w') as log:
  r=subprocess.run(['python3','-B','-W','error','work/run-nats-focused-38.py',str(path)],stdout=log,stderr=subprocess.STDOUT)
 r.check_returncode()
 for case in json.loads(path.read_text())['cases']:
  status=json.loads((Path('results')/case['name']/'status.json').read_text())
  assert status['exit_code']==(0 if variant=='integration' else 1),(case['name'],status['exit_code'])
 print(variant,'completed with expected exit codes',flush=True)
