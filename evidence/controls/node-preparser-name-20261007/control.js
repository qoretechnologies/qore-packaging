// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert = require('node:assert/strict');
let checks = 0;
const forms = ['function', 'function*', 'async function', 'async function*'];
async function value(fn, form, x) {
    const result = fn(x);
    if (form.includes('*')) {
        const step = await result.next();
        assert.equal(step.done, false);
        const end = await result.next();
        assert.equal(end.done, true);
        return step.value;
    }
    return await result;
}
(async () => {
    for (let repeat = 0; repeat < 150; ++repeat) {
        for (const form of forms) {
            for (const name of ['declared', 'async', 'π', '$value']) {
                const statement = form.includes('*') ? 'yield a + x;' : 'return a + x;';
                const make = new Function('a', `${form} ${name}(x) { ${statement} } return ${name};`);
                const fn = make(repeat);
                assert.equal(fn.name, name);
                assert.equal(await value(fn, form, 7), repeat + 7);
                ++checks;
            }
        }
        for (const source of [
            'function () {}', 'async function () {}', 'function* () {}',
            'async function* () {}', 'function 123() {}',
            '"use strict"; function eval() {}',
            '"use strict"; function arguments() {}',
            'function for() {}',
        ]) {
            assert.throws(() => new Function(source), SyntaxError);
            ++checks;
        }
        // These names are valid in sloppy ordinary declarations.
        for (const name of ['eval', 'arguments']) {
            const fn = new Function(`function ${name}(x) { return x + 1; } return ${name};`)();
            assert.equal(fn(7), 8);
            ++checks;
        }
    }
    for (let repeat = 0; repeat < 20; ++repeat) {
        for (const form of forms) {
            for (const name of ['', 'named']) {
                const statement = form.includes('*') ? 'yield x + 3;' : 'return x + 3;';
                const source = `export default ${form} ${name}(x) { ${statement} } // ${repeat}`;
                const ns = await import('data:text/javascript,' + encodeURIComponent(source));
                assert.equal(ns.default.name, name || 'default');
                assert.equal(await value(ns.default, form, repeat), repeat + 3);
                ++checks;
            }
        }
        for (const source of [
            'export default function eval() {}',
            'export default async function arguments() {}',
            'export default function* for() {}',
            'export default function () {}; export default 1;',
        ]) {
            await assert.rejects(import('data:text/javascript,' + encodeURIComponent(source + ` // ${repeat}`)), SyntaxError);
            ++checks;
        }
    }
    console.log(`PASS: ${checks} declaration, lazy-body, default-export and syntax-rejection checks`);
})().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
