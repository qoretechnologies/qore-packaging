# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import os
import re
import subprocess

root = Path.cwd()
repo = root.parent / 'qore'
build = repo / 'build-debug'
out = root / 'results/core-date-docs2-20261007'
out.mkdir()
env = os.environ.copy()
env.pop('LD_PRELOAD', None)
env['LD_LIBRARY_PATH'] = str(build)
env['QORE_BINARY'] = str(build / 'qore')
env['QORE_MODULE_DIR_ONLY'] = '1'
env['QORE_MODULE_DIR'] = ':'.join([str(repo / 'qlib'), *(str(p) for p in (build / 'modules').iterdir() if p.is_dir()), str(repo.parent / 'module-xml/build')])
header = (repo / 'include/qore/DateTime.h').read_text()
section = header[header.index('//! returns a newly allocated sum'):header.index('DLLEXPORT DateTime* subtractBy')]
example = re.search(r'@code\{.cpp\}\n(.*?)@endcode', section, re.S)[1]
source = out / 'invoice.cpp'
source.write_text('''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <qore/Qore.h>
#include <memory>
#include <stdexcept>
struct Runtime {
    Runtime() { qore_init(QL_MIT, "UTF-8", false, QLO_DISABLE_SIGNAL_HANDLING); }
    ~Runtime() { qore_cleanup(); }
};
int main() {
    Runtime runtime;
''' + example + '''
    if (!due_date->isEqual(DateTime(nullptr, "2026-11-07T09:00:00Z"))) {
        throw std::runtime_error("invoice due date differs from documented calendar sum");
    }
}
''')
commands = [('invoice-build', ['c++', '-std=c++20', '-Wall', '-Werror', '-I'+str(build/'include'),
            '-I'+str(repo/'include'), str(source), '-L'+str(build), '-lqore', '-o', str(out/'invoice')]),
            ('invoice', [str(out/'invoice')])]
for name in ['qore/vars/timezone-date-errors.qtest', 'qore/misc/date-format-codes.qtest']:
    commands.append((Path(name).stem, [str(build/'qore'), '-b', '--enable-debug', str(repo/'examples/test'/name)]))
rows=[]
# Re-run only the test affected by the missing local XML module path.
commands = [row for row in commands if row[0] == 'date-format-codes']
for name, cmd in commands:
    r=subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=180)
    output=r.stdout+r.stderr
    (out/(name+'.log')).write_text(output)
    rows.append({'name':name,'command':cmd,'exit_code':r.returncode})
    (out/'status.json').write_text(json.dumps(rows,indent=2)+'\n')
    assert r.returncode==0 and not re.search(r'(?i)warning:|error:|FAIL|Skipped:',output),output
    print(name,'PASS',flush=True)
