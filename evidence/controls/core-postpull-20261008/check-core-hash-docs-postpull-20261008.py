# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import os
import re
import subprocess

root = Path.cwd()
repo = root.parent / 'qore'
out = root / 'results/core-hash-docs-postpull-20261008'
out.mkdir()
header = (repo / 'include/qore/QoreHashNode.h').read_text()
example, = re.findall(r'@code\{\.cpp\}\n(.*?)\n\s*@endcode', header, re.S)
fixture = '''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <qore/Qore.h>
#include <cstdio>
static void lookup() {
    ExceptionSink xsink;
    ReferenceHolder<QoreHashNode> holder(new QoreHashNode(autoTypeInfo), &xsink);
    QoreHashNode& accounts = **holder;
    accounts.setKeyValue("caf\\xc3\\xa9", QoreValue(int64(73)), &xsink);
'''
fixture += example
fixture += '\n}\nint main() {\n    qore_init(QL_MIT, "UTF-8", false, QLO_DISABLE_SIGNAL_HANDLING);\n    lookup();\n    qore_cleanup();\n}\n'
(out / 'example.cpp').write_text(fixture)
records = []
for mode, folder in [('debug', 'build-debug'), ('release', 'build')]:
    build = repo / folder
    executable = out / mode
    commands = [('compile', ['g++', '-std=c++17', '-Wall', '-Werror', '-O2', '-g', '-I', str(build / 'include'),
                            '-I', str(repo / 'include'), str(out / 'example.cpp'), '-L', str(build), '-lqore', '-o', str(executable)]),
                ('run', [str(executable)])]
    for step, command in commands:
        env = os.environ.copy()
        env['LD_LIBRARY_PATH'] = str(build)
        result = subprocess.run(command, env=env, capture_output=True)
        (out / (mode + '-' + step + '.log')).write_bytes(result.stdout + result.stderr)
        records.append({'mode': mode, 'step': step, 'command': command, 'exit_code': result.returncode})
        (out / 'status.json').write_text(json.dumps(records, indent=2) + '\n')
        result.check_returncode()
        assert not result.stderr
        assert result.stdout == (b'Account balance: 73\n' if step == 'run' else b'')
print('Both documented example builds and runs pass')
