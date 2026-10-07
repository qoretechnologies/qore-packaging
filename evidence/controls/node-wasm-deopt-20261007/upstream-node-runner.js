// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
globalThis.print = (...args) => console.log(...args);
globalThis.d8 = {file: {execute(path) { vm.runInThisContext(fs.readFileSync(path, 'utf8'), {filename: path}); }}};
d8.file.execute('test/mjsunit/mjsunit.js');
d8.file.execute(process.argv[2]);
console.log('PASS: ' + process.argv[2]);
