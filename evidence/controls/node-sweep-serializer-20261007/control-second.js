// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert = require('node:assert/strict');
const vm = require('node:vm');
let checks = 0;
for (let iteration = 0; iteration < 50; ++iteration) {
  const source = `function outer(x) { return function inner(y) { return x + y + ${iteration}; }; } outer;`;
  const script = new vm.Script(source);
  for (let phase = 0; phase < 3; ++phase) {
    if (phase > 0) {
      const original = script.runInNewContext()(17);
      for (let warm = 0; warm < (phase === 1 ? 1 : 1000); ++warm) {
        assert.equal(original(warm), 17 + warm + iteration);
        ++checks;
      }
    }
    const cache = script.createCachedData();
    assert.ok(cache.length > 0);
    const restored = new vm.Script(source, {cachedData: cache, filename: `restored-${iteration}-${phase}.js`});
    assert.equal(restored.cachedDataRejected, false);
    const inner = restored.runInNewContext()(31);
    for (let value = 0; value < 32; ++value) {
      assert.equal(inner(value), 31 + value + iteration);
      ++checks;
    }
    const broken = Buffer.from(cache);
    broken[0] ^= 0xff;
    assert.equal(new vm.Script(source, {cachedData: broken, filename: `broken-${iteration}-${phase}.js`}).cachedDataRejected, true);
    assert.equal(new vm.Script(source + '\n', {cachedData: cache}).cachedDataRejected, true);
    checks += 2;
  }
  let buffers = Array.from({length: 256}, (_, i) => {
    const view = new Uint8Array(new ArrayBuffer(16384));
    view[0] = i;
    view[view.length - 1] = 255 - i;
    return view;
  });
  gc({type: 'minor', execution: 'sync'});
  for (let i = 0; i < buffers.length; ++i) {
    assert.equal(buffers[i][0], i);
    assert.equal(buffers[i][buffers[i].length - 1], 255 - i);
    checks += 2;
  }
  buffers = null;
  gc({type: 'major', execution: 'sync'});
}
console.log(`PASS: ${checks} actual code-cache and ArrayBuffer GC checks`);
