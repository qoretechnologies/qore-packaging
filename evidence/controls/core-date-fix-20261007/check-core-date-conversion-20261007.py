# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import re
import shlex
import subprocess
import tempfile

root = Path.cwd()
repo = root.parent / 'qore'
out = root / 'results/core-date-conversion-20261007'
out.mkdir()
flags_text = (repo / 'build/CMakeFiles/libqore.dir/flags.make').read_text()
flags = []
for key in ('CXX_DEFINES', 'CXX_INCLUDES', 'CXX_FLAGS'):
    flags += shlex.split(re.search(r'^' + key + r' = (.*)$', flags_text, re.M)[1])
source = (repo / 'lib/DateTime.cpp').read_text()
assert source.count('rv->priv->add(*dt.priv);') == 1
records = []
with tempfile.TemporaryDirectory(prefix='qore-date-conversion-') as temporary:
    for mode in ('fixed', 'old-pointer-call'):
        path = Path(temporary) / (mode + '.cpp')
        path.write_text(source if mode == 'fixed' else source.replace(
            'rv->priv->add(*dt.priv);', 'rv->priv->add(dt.priv);'))
        command = ['c++', *flags, '-fsyntax-only', str(path)]
        result = subprocess.run(command, cwd=repo, capture_output=True, text=True, timeout=120)
        (out / (mode + '.log')).write_text(result.stdout + result.stderr)
        if mode == 'fixed':
            assert result.returncode == 0 and not result.stderr, result.stderr
        else:
            assert result.returncode != 0
            assert 'cannot convert' in result.stderr and 'qore_date_private*' in result.stderr
            assert result.stderr.count('error:') == 1, result.stderr
        records.append({'mode': mode, 'command': command, 'exit_code': result.returncode})
(out / 'status.json').write_text(json.dumps(records, indent=2) + '\n')
print('PASS: actual fixed DateTime source compiles; old pointer call is rejected by the explicit constructor')
