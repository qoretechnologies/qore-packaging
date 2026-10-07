// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert = require('node:assert/strict');
assert.equal(%IsMaglevEnabled(), true);
let checks = 0;
function nested(i) {
    const child = {x: i, y: i + 0.25};
    return {child, sibling: {z: -i}, value: i + 0.5};
}
function doubles(i) {
    const array = [1.25, 2.5, 3.75];
    array[1] = i + 0.25;
    return {array, length: array.length};
}
function cons(i, left, right) {
    const s = left + right;
    return {text: s, length: s.length, index: i};
}
function number(i) {
    const n = i + 0.25;
    return {first: n, second: {value: n * 2}};
}
const left = 'a'.repeat(128);
const right = 'b'.repeat(129);
const cases = [
    [nested, (v, i) => {
        assert.equal(v.child.x, i);
        assert.equal(v.child.y, i + 0.25);
        assert.equal(v.sibling.z, -i);
        assert.equal(v.value, i + 0.5);
    }],
    [doubles, (v, i) => {
        assert.deepEqual(v.array, [1.25, i + 0.25, 3.75]);
        assert.equal(v.length, 3);
    }],
    [cons, (v, i) => {
        assert.equal(v.text, left + right);
        assert.equal(v.length, 257);
        assert.equal(v.index, i);
    }],
    [number, (v, i) => {
        assert.equal(v.first, i + 0.25);
        assert.equal(v.second.value, (i + 0.25) * 2);
    }],
];
for (const [fn, verify] of cases) {
    %PrepareFunctionForOptimization(fn);
    for (let i = 0; i < 20; ++i) {
        verify(fn(i, left, right), i);
    }
    %OptimizeMaglevOnNextCall(fn);
    verify(fn(21, left, right), 21);
    assert.equal(%ActiveTierIsMaglev(fn), true);
    const retained = [];
    for (let i = 0; i < 4000; ++i) {
        const input = i % 2 ? -i : i;
        const value = fn(input, left, right);
        verify(value, input);
        if (i % 100 === 0) {
            retained.push([value, input]);
            global.gc();
        }
        ++checks;
    }
    assert.equal(%ActiveTierIsMaglev(fn), true);
    global.gc();
    for (const [value, input] of retained) {
        verify(value, input);
        ++checks;
    }
}
console.log(`PASS: ${checks} Maglev allocation and post-GC lifetime cases`);
