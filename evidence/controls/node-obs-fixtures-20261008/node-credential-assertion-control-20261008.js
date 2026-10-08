// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert = require('node:assert');
const fs = require('node:fs');
const vm = require('node:vm');
const text = fs.readFileSync(process.argv[2], 'utf8');
const start = text.indexOf("  assert.throws(() => {\n    process.seteuid('nobody');");
assert.notStrictEqual(start, -1);
const end = text.indexOf('\n\n  return;', start);
assert(end > start);
const source = text.slice(start, end);
const fixtures = [
  ['missing user', true, 'ERR_UNKNOWN_CREDENTIAL', 'User identifier does not exist: nobody'],
  ['denied user', true, 'EPERM', 'EPERM, Operation not permitted'],
  ['wrong user', false, 'ERR_UNKNOWN_CREDENTIAL', 'User identifier does not exist: root'],
  ['wrong code', false, 'EINVAL', 'User identifier does not exist: nobody'],
  ['wrong message', false, 'EPERM', 'unrelated failure'],
  ['missing exception', false, null, null],
  ['missing error code', false, undefined, 'User identifier does not exist: nobody'],
];
for (const [label, accepted, code, message] of fixtures) {
  let calls = 0;
  const run = () => vm.runInNewContext(source, { assert, process: { seteuid(user) {
    ++calls;
    assert.strictEqual(user, 'nobody');
    if (code === null) return;
    throw Object.assign(new Error(message), { code });
  } } });
  if (accepted) run();
  else assert.throws(run, { code: 'ERR_ASSERTION' });
  assert.strictEqual(calls, 1);
  console.log('PASS:', label);
}
