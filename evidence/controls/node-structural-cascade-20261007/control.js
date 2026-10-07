// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert = require('node:assert/strict');
let checks = 0;
for (let length = 1; length <= 7; ++length) {
    for (let mode = 0; mode < 4; ++mode) {
        const values = Array.from({length}, (_, i) => i === 0 ? 0 : 100 - i * 7);
        if (mode === 1 && length > 2) {
            values[length - 1] = 0;
        }
        const source = values.map((v, i) =>
            `${mode === 2 ? 'state.n++;' : ''}if (${mode === 3 && i === 2 ? 'y' : 'x'} === ${v}) return ${i};`
        ).join('\n') + '\nreturn -1;';
        const fn = new Function('x', 'y', 'state', source);
        const inputs = [-2147483648, -1, 0, 1, 51, 58, 65, 72, 79, 86, 93, 100, 2147483647];
        const verify = (x, y) => {
            let expected = -1;
            let calls = 0;
            for (let i = 0; i < values.length; ++i) {
                if (mode === 2) {
                    ++calls;
                }
                if ((mode === 3 && i === 2 ? y : x) === values[i]) {
                    expected = i;
                    break;
                }
            }
            const state = {n: 0};
            assert.equal(fn(x, y, state), expected);
            assert.equal(state.n, calls);
            ++checks;
        };
        %PrepareFunctionForOptimization(fn);
        for (const x of inputs) {
            for (const y of inputs) {
                verify(x, y);
            }
        }
        %OptimizeFunctionOnNextCall(fn);
        verify(0, 1);
        assert.equal(%ActiveTierIsTurbofan(fn), true);
        for (let repeat = 0; repeat < 20; ++repeat) {
            for (const x of inputs) {
                for (const y of inputs) {
                    verify(x, y);
                }
            }
        }
        assert.equal(%ActiveTierIsTurbofan(fn), true);
    }
}
console.log(`PASS: ${checks} optimized branch-cascade and side-effect checks`);
