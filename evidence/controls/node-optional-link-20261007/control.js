// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert = require('node:assert/strict');
let checks = 0;
const chain = new Function('o', 'key', 'arg', 'return o?.a?.[key()]?.(arg());');
for (let repeat = 0; repeat < 1000; ++repeat) {
    for (let mode = 0; mode < 10; ++mode) {
        let gets = 0, keys = 0, args = 0, calls = 0;
        const child = {base: repeat};
        let property;
        if (mode === 4) {
            property = null;
        } else if (mode === 5) {
            property = undefined;
        } else if (mode === 6) {
            property = 42;
        } else {
            property = function(x) {
                ++calls;
                assert.equal(this, child);
                return this.base + x;
            };
        }
        Object.defineProperty(child, 'π', {get() { ++gets; return property; }});
        let root;
        if (mode === 0) {
            root = null;
        } else if (mode === 1) {
            root = undefined;
        } else if (mode === 2) {
            root = {a: null};
        } else if (mode === 3) {
            root = {a: undefined};
        } else if (mode === 8) {
            root = 0;
        } else if (mode === 9) {
            root = false;
        } else {
            root = {a: child};
        }
        const invoke = () => chain(root, () => { ++keys; return 'π'; }, () => { ++args; return 3; });
        if (mode === 6) {
            assert.throws(invoke, TypeError);
        } else {
            assert.equal(invoke(), mode === 7 ? repeat + 3 : undefined);
        }
        assert.equal(keys, mode >= 4 && mode <= 7 ? 1 : 0);
        assert.equal(gets, keys);
        assert.equal(args, mode === 6 || mode === 7 ? 1 : 0);
        assert.equal(calls, mode === 7 ? 1 : 0);
        ++checks;
    }
    // Parentheses end a chain; a missing ordinary property still throws.
    for (const root of [null, undefined]) {
        assert.equal(root?.a.b, undefined);
        assert.throws(() => (root?.a).b, TypeError);
        ++checks;
    }
    for (const root of [{a: null}, {a: undefined}]) {
        assert.throws(() => root?.a.b, TypeError);
        assert.equal(root?.a?.b, undefined);
        ++checks;
    }
    class Value {
        #value = repeat;
        read(other) { return other?.#value; }
    }
    const value = new Value();
    assert.equal(value.read(value), repeat);
    assert.equal(value.read(null), undefined);
    assert.throws(() => value.read({}), TypeError);
    ++checks;
    for (const source of [
        'o?.?.a', 'o?..a', 'o?.a`text`', 'o?.`text`',
        'new o?.Ctor()', 'o?.a = 1', 'o?.a++', 'o?.[',
    ]) {
        assert.throws(() => new Function('o', source), SyntaxError);
        ++checks;
    }
}
console.log(`PASS: ${checks} optional-chain result, side-effect and syntax checks`);
