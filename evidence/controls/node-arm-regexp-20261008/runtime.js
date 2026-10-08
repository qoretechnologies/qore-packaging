// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert = require('node:assert/strict');
const isWord = c => (c >= 48 && c <= 57) || (c >= 65 && c <= 90) || (c >= 97 && c <= 122) || c === 95;
const isDigit = c => c >= 48 && c <= 57;
const isLine = c => c === 10 || c === 13 || c === 0x2028 || c === 0x2029;
const isSpace = c => (c >= 9 && c <= 13) || c === 32 || c === 160 || c === 0x1680 || (c >= 0x2000 && c <= 0x200a) || c === 0x2028 || c === 0x2029 || c === 0x202f || c === 0x205f || c === 0x3000 || c === 0xfeff;
const cases = [
  ['\\s', '', isSpace], ['\\S', '', c => !isSpace(c)],
  ['\\w', '', isWord], ['\\W', '', c => !isWord(c)],
  ['\\d', '', isDigit], ['\\D', '', c => !isDigit(c)],
  ['[\\n\\r\\u2028\\u2029]', '', isLine], ['.', '', c => !isLine(c)],
  ['.', 's', () => true],
];
let checks = 0;
for (const prefix of ['', '\u0100']) {
  for (const [pattern, flags, expected] of cases) {
    // Negative lookahead gives an exact end-of-input check, including newlines.
    const regexp = new RegExp(`^${prefix}(?:${pattern})(?![\\s\\S])`, flags);
    for (let c = 0; c <= 0xffff; ++c) {
      const input = prefix + String.fromCharCode(c);
      assert.equal(regexp.test(input), expected(c), `${pattern} prefix=${prefix.length} code=${c}`);
      ++checks;
    }
    for (const input of [prefix, prefix + 'ab', prefix + '\n\r']) {
      assert.equal(regexp.test(input), false);
      ++checks;
    }
  }
}
console.log(JSON.stringify({node:process.version,arch:process.arch,checks,result:'pass'}));
