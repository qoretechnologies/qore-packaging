# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import os
import re
import shlex
import subprocess
import tempfile

root = Path.cwd()
repo = root.parent / 'qore'
out = root / 'results/core-relative-sign-matrix-final-20261007'
out.mkdir()
source = root / 'work/core-relative-sign-control-20261007.cpp'
flags_text = (repo / 'build/CMakeFiles/libqore.dir/flags.make').read_text()
flags = []
for key in ('CXX_DEFINES', 'CXX_INCLUDES', 'CXX_FLAGS'):
    flags += shlex.split(re.search(r'^' + key + r' = (.*)$', flags_text, re.M)[1])
rows = []
env = os.environ.copy()
env.pop('LD_PRELOAD', None)
env['LD_LIBRARY_PATH'] = str(repo / 'build-debug')


def run(name, command):
    result = subprocess.run(command, cwd=repo, env=env, capture_output=True, text=True, timeout=180)
    (out / (name + '.log')).write_text(result.stdout + result.stderr)
    rows.append({'name': name, 'command': command, 'exit_code': result.returncode})
    return result


with tempfile.TemporaryDirectory(prefix='qore-relative-sign-') as temporary:
    temp = Path(temporary)
    header = temp / 'qore/intern/qore_date_private.h'
    header.parent.mkdir(parents=True)
    header.write_bytes(subprocess.check_output(['git', 'show', '3c0fe14805c41cf1a0b8978546b8c13cc218d0a2:include/qore/intern/qore_date_private.h'], cwd=repo))
    for mode, options in [('original', ['-I' + str(temp)]), ('fixed', []),
                          ('ubsan', ['-fsanitize=undefined', '-fno-sanitize-recover=all'])]:
        binary = temp / mode
        result = run(mode + '-build', ['c++', *options, *flags, str(source), '-L' + str(repo / 'build-debug'),
                                      '-lqore', '-o', str(binary)])
        assert result.returncode == 0 and not result.stderr, result.stderr
        result = run(mode, [str(binary)])
        if mode == 'original':
            assert result.returncode == 1 and 'FAIL:' in result.stderr
        else:
            assert result.returncode == 0 and result.stdout == 'PASS: 679 signed-duration boundary cases\n'
            assert not result.stderr
        if mode == 'fixed':
            result = run('valgrind', ['valgrind', '--error-exitcode=99', '--leak-check=full',
                '--show-leak-kinds=all', '--errors-for-leak-kinds=definite,indirect,possible', str(binary)])
            assert result.returncode == 0
            assert 'ERROR SUMMARY: 0 errors' in result.stderr
            for kind in ('definitely', 'indirectly', 'possibly'):
                assert re.search(kind + r' lost:\s+0 bytes in 0 blocks', result.stderr)
            for warning in re.findall(r'(?im)^.*warning:.*$', result.stderr):
                assert 'Warning: zero subprog, missing DW_AT_abstract_origin in DW_TAG_inlined_subroutine in ' + str(repo / 'build-debug/libqore.so.20.0.0') in warning, warning
(out / 'status.json').write_text(json.dumps(rows, indent=2) + '\n')
print('PASS: original fails; 679 cases pass with the fixed header, UBSan and Valgrind')
