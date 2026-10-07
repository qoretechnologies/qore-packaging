// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert = require('node:assert/strict');
const masks = [0, 127, 255, 32767, 65535, 2147483647, -2147483648, -1];
const comparisons = [-1, 0, 127, 128, 255, 256, 32767, 32768, 65535, 65536, 2147483647, 2147483648];
const values = [-2147483648, -65536, -1, 0, 1, 127, 128, 255, 256, 32767, 32768, 65535, 65536, 2147483647];
const operators = ['===', '!==', '<', '<=', '>', '>='];
function reference(value, mask, constant, operator) {
  const left = BigInt.asIntN(32, BigInt(value) & BigInt(mask));
  const right = BigInt(constant);
  switch (operator) {
    case '===': return left === right;
    case '!==': return left !== right;
    case '<': return left < right;
    case '<=': return left <= right;
    case '>': return left > right;
    case '>=': return left >= right;
    default: throw new Error('Invalid test operator');
  }
}
let checks = 0;
for (const mask of masks) {
  for (const constant of comparisons) {
    for (const operator of operators) {
      const fn = new Function('value', `return (value & ${mask}) ${operator} ${constant};`);
      %PrepareFunctionForOptimization(fn);
      for (const value of values) {
        assert.equal(fn(value), reference(value, mask, constant, operator));
      }
      %OptimizeFunctionOnNextCall(fn);
      for (let repeat = 0; repeat < 100; ++repeat) {
        for (const value of values) {
          assert.equal(fn(value), reference(value, mask, constant, operator));
          ++checks;
        }
      }
      // runtime.h: kOptimized and kTurboFanned; require actual optimized execution.
      assert.equal(%GetOptimizationStatus(fn) & 80, 80);
    }
  }
}
console.log(`PASS: ${checks} actual optimized masked comparison checks`);
