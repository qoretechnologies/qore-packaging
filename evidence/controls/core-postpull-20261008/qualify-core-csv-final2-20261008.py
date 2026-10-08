# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Complete functional qualification; retain the already-pending configure diagnostics."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess

root = Path(__file__).resolve().parent.parent
repo = root.parent / 'qore'
prior = root / 'results/core-csv-postpull-20261008'
out = root / 'results/core-csv-final2-20261008'
out.mkdir()
pins = json.loads((prior / 'source.json').read_text())
pins['examples/test/qlib/CsvUtil/CsvProfiler.qtest'] = hashlib.sha256((repo / 'examples/test/qlib/CsvUtil/CsvProfiler.qtest').read_bytes()).hexdigest()
assert pins == {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in pins}
steps = json.loads((prior / 'steps.json').read_text())
assert len(steps) == 1 and steps[0]['name'] == 'build' and steps[0]['exit_code'] == 0
pending = []


def diagnostics(log, name):
    blocks = re.findall(r'CMake Warning at [^\n]+\n  ([^\n]+)', log)
    if blocks:
        assert sorted(blocks) == sorted([
            'libngtcp2_crypto_quictls library is disabled due to lack of good quictls',
            'libngtcp2_crypto_libressl library is disabled due to lack of good LibreSSL'])
        pending.append({'step': name, 'diagnostics': blocks, 'approval': 'Pending user decision'})
    rest = re.sub(r'CMake Warning at [^\n]+\n  [^\n]+', '', log)
    assert not re.search(r'(?im)(warning encountered|^warning:|^error:|CMake Warning|CMake Error)', rest)


diagnostics((prior / 'debug/build.log').read_text(), 'prior-debug-build')
records = []
result = {'exit_code': 1}
try:
    for mode, folder in [('debug', 'build-debug'), ('release', 'build')]:
        build = repo / folder
        env = os.environ.copy()
        env.update(LD_LIBRARY_PATH=str(build), QORE_BINARY=str(build / 'qore'), QORE_BIN=str(build / 'qore'),
                   QORE_LIBDIR=str(build), QORE_MODULE_DIR=':'.join([str(repo / 'qlib'),
                   *[str(p) for p in (build / 'modules').iterdir() if p.is_dir()]]))
        directory = out / mode
        directory.mkdir()
        commands = [] if mode == 'debug' else [('build', ['cmake', '--build', str(build), '--target', 'CsvUtil-qmod', '-j2'])]
        commands += [(p.stem, [str(build / 'qore'), '-b', '--enable-debug', str(p), '-v'])
                     for p in sorted((repo / 'examples/test/qlib/CsvUtil').glob('*.qtest'))]
        for name, command in commands:
            with (directory / (name + '.log')).open('x') as stream:
                process = subprocess.run(command, cwd=repo, env=env, stdout=stream, stderr=subprocess.STDOUT)
            records.append({'mode': mode, 'name': name, 'exit_code': process.returncode, 'command': command})
            (out / 'steps.json').write_text(json.dumps(records, indent=2) + '\n')
            print(mode, name, process.returncode, flush=True)
            process.check_returncode()
            log = (directory / (name + '.log')).read_text()
            diagnostics(log, mode + '-' + name)
            if name != 'build':
                match = re.search(r'Ran (\d+) test cases?, (\d+) succeeded \((\d+) assertions\)', log)
                assert match and match[1] == match[2], name
    assert pins == {p: hashlib.sha256((repo / p).read_bytes()).hexdigest() for p in pins}
    result['exit_code'] = 0
except BaseException as error:
    result['error'] = repr(error)
    raise
finally:
    result['source_sha256'] = pins
    result['pending_diagnostics'] = pending
    (out / 'status.json').write_text(json.dumps(result, indent=2) + '\n')
