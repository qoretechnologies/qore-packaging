#!/usr/bin/env python3
# Copyright 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Exercise real V8 GC with and without forced compaction and verbose tracing."""
import json
from pathlib import Path
import re
import subprocess
import sys

PROGRAM = r'''
'use strict';
const assert = require('node:assert/strict');
for (let round = 0; round < 3; ++round) {
  globalThis.live = Array.from({ length: 40000 }, (_, value) => ({
    value, text: 'allocation-' + value + '-'.repeat(64)
  }));
  global.gc();
  globalThis.live = globalThis.live.filter(({ value }) => value % 8 === 0);
  global.gc();
  assert.equal(globalThis.live.length, 5000);
  for (let i = 0; i < globalThis.live.length; ++i) {
    assert.equal(globalThis.live[i].value, i * 8);
    assert.equal(globalThis.live[i].text, 'allocation-' + i * 8 + '-'.repeat(64));
  }
}
globalThis.live = null;
global.gc();
console.log('COMPACTION_TRACE_CONTROL_PASS');
'''


def check(node: str) -> list[dict]:
    results = []
    for name, flags in (
        ('ordinary', []),
        ('standard-trace', ['--trace-fragmentation-verbose']),
        ('forced-trace', ['--compact-on-every-full-gc', '--trace-fragmentation-verbose']),
    ):
        command = [node, '--expose-gc', *flags, '--eval', PROGRAM]
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode or result.stderr:
            raise AssertionError((name, result.returncode, result.stdout, result.stderr))
        if result.stdout.count('COMPACTION_TRACE_CONTROL_PASS') != 1:
            raise AssertionError((name, 'missing completed GC/data checks', result.stdout))
        pages = [line for line in result.stdout.splitlines() if 'compaction-selection-page:' in line]
        if name == 'ordinary':
            if pages:
                raise AssertionError(('trace emitted without flag', pages))
        elif not pages:
            raise AssertionError((name, 'no traced candidate pages', result.stdout))
        elif name == 'forced-trace':
            for line in pages:
                if ('mode=compact-on-every-full-gc' not in line
                        or 'fragmentation_limit_' in line or 'compaction_limit_' in line):
                    raise AssertionError(('forced mode read unused thresholds', line))
        else:
            for line in pages:
                match = re.search(r'fragmentation_limit_kb=(\d+) fragmentation_limit_percent=(\d+) '
                                  r'sum_compaction_kb=(\d+) compaction_limit_kb=(\d+)', line)
                if not match or not 0 <= int(match[2]) <= 100 or 'mode=' in line:
                    raise AssertionError(('invalid standard heuristic trace', line))
        results.append({'mode': name, 'traced_pages': len(pages), 'value_assertions': 30003})
    return results


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: nodejs24-compaction-trace-test.py /path/to/node')
    print(json.dumps(check(str(Path(sys.argv[1]).resolve())), indent=2))
