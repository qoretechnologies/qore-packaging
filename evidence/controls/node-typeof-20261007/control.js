// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert = require('node:assert/strict');
const words = ['number', 'string', 'symbol', 'bigint', 'boolean', 'undefined', 'function', 'object', 'invalid'];
const values = [0, -1, NaN, Infinity, '', 'x', Symbol('x'), 0n, 123n, true, false,
                undefined, null, () => 1, {}, [], new Number(1), new String('x'),
                new Proxy(() => 1, {}), new Proxy({}, {})];
let checks = 0;
for (const word of words) {
  const test = new Function('value', `return typeof value === ${JSON.stringify(word)};`);
  %PrepareFunctionForOptimization(test);
  for (const value of values) {
    assert.equal(test(value), typeof value === word);
  }
  %OptimizeFunctionOnNextCall(test);
  for (let repeat = 0; repeat < 1000; ++repeat) {
    for (const value of values) {
      assert.equal(test(value), typeof value === word);
      ++checks;
    }
  }
  // V8 runtime.h: kOptimized = 1 << 4, kTurboFanned = 1 << 6.
  const status = %GetOptimizationStatus(test);
  assert.equal(status & ((1 << 4) | (1 << 6)), (1 << 4) | (1 << 6), word);
}
console.log(`PASS: ${checks} actual optimized typeof comparison checks`);
