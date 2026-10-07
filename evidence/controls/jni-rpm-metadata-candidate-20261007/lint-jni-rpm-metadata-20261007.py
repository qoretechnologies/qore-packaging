# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess,sys
root=Path.cwd();label=sys.argv[1]
path=root/('results/leap-jni-rpm-final-3' if label=='original' else 'results/leap-jni-rpm-metadata-candidate-20261007')
record=json.loads((path/'build.json').read_text());assert record['exit_code']==0
rpms=[p for p in sorted((path/'rpmbuild').glob('RPMS/*/*.rpm')) if 'debug' not in p.name]
rpms+=sorted((path/'rpmbuild/SRPMS').glob('*.src.rpm'))
assert len(rpms)==5
cmd=['docker','run','--rm','--init','--network','none','-v',str(path)+':/rpms:ro',
 'qore-rpm-keep:leap-debugedit-lint-1','rpmlint',*[str(Path('/rpms')/p.relative_to(path)) for p in rpms]]
with (root/f'results/jni-rpm-metadata-{label}-lint-20261007.log').open('x') as log:
 result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=600)
(root/f'results/jni-rpm-metadata-{label}-lint-status-20261007.json').write_text(json.dumps({'command':cmd,'exit_code':result.returncode},indent=2)+'\n')
print(label,'lint exit',result.returncode)
