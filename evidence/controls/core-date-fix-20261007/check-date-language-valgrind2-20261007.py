# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json
import os
import re
import subprocess

root = Path.cwd()
repo = root.parent / 'qore'
build = repo / 'build-debug'
out = root / 'results/core-date-language-valgrind2-20261007'
out.mkdir()
native = root / 'results/core-date-add-final-tests-20261007/debug/native.log'
assert native.read_text() == 'PASS: 1836 DateTime addition cases\n'
env = os.environ.copy()
env.pop('LD_PRELOAD', None)
env['LD_LIBRARY_PATH'] = str(build)
env['QORE_BINARY'] = str(build / 'qore')
env['QORE_MODULE_DIR_ONLY'] = '1'
env['QORE_INCLUDE_DIR'] = ''
env['QORE_MODULE_DIR'] = ':'.join([str(repo / 'qlib'),
    *(str(p) for p in sorted((build / 'modules').iterdir()) if p.is_dir()),
    str(repo.parent / 'module-xml/build')])
command = ['valgrind', '--error-exitcode=99', '--leak-check=full', '--show-leak-kinds=all',
           '--errors-for-leak-kinds=definite,indirect,possible', '--track-origins=yes', str(build / 'qore'), '-b', '--enable-debug',
           str(repo / 'examples/test/qore/vars/date-add-native.qtest')]
with (out / 'test.log').open('x') as stream:
    result = subprocess.run(command, cwd=repo, env=env, stdout=stream, stderr=subprocess.STDOUT)
(out / 'status.json').write_text(json.dumps({'command': command, 'exit_code': result.returncode}, indent=2) + '\n')
text = (out / 'test.log').read_text()
# The one report matches the already approved Fedora PCRE2 QUnit suffix scan.
# Preserve it in full and reject every additional error context or lost allocation.
assert result.returncode == 99, text[-4000:]
assert 'Ran 2 test cases, 2 succeeded (29 assertions)' in text
assert 'ERROR SUMMARY: 1 errors from 1 contexts (suppressed: 0 from 0)' in text
assert text.count('Conditional jump or move depends on uninitialised value(s)') == 1
assert 'at 0x5B965DA: ???' in text
assert 'qore_get_thread_call_stack()' in text
for kind in ('definitely', 'indirectly', 'possibly'):
    assert re.search(kind + r' lost:\s+0 bytes in 0 blocks', text)
for warning in re.findall(r'(?im)^.*warning:.*$', text):
    assert 'Warning: zero subprog, missing DW_AT_abstract_origin in DW_TAG_inlined_subroutine in ' + str(build / 'libqore.so.20.0.0') in warning, warning
assert not re.search(r'(?i)skipped|FAIL', text)
print('PASS: 2 cases / 29 assertions; zero lost allocations; only the verified, previously approved PCRE2 and GCC diagnostics')
