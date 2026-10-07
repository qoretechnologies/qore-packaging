// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert = require('node:assert/strict');
const patterns = ['a', '(?<=a)b', '(?<!a)b', 'a(?=b)', 'a(?!b)',
  '(?=(a+))a', '(?<=(a))b', '(?<=a)(?=b)b', '(?<=(?<=a)b)c',
  '(?=(a(?=b)))ab', '(?!(a))b', '((?<=a)b|c)', '(a+)(?=b)',
  '(?<=ab)c|a(?=bc)', '(?<=a)(b*)(?=c)'];
const inputs=[''];
for(let length=1;length<=5;++length) {
  for(let bits=0;bits<3**length;++bits) {
    let n=bits, s='';for(let i=0;i<length;++i) {s+='abc'[n%3];n=Math.floor(n/3);}inputs.push(s);
  }
}
let checks=0;
for(let repeat=0;repeat<5;++repeat) {
  for(const pattern of patterns) {
    const baseline=new RegExp(pattern), linear=new RegExp(pattern,'l');
    for(const input of inputs) {
      const a=baseline.exec(input), b=linear.exec(input);
      assert.deepStrictEqual(b,a);++checks;
    }
  }
}
for(const pattern of ['(?<=', '(?=)', '[', '(?<(a))', 'a{2,1}']) {
  if(pattern==='(?=)') {assert.deepStrictEqual(new RegExp(pattern,'l').exec(''), /(?=)/.exec(''));}
  else {assert.throws(()=>new RegExp(pattern,'l'), SyntaxError);}
  ++checks;
}
console.log(`PASS: ${checks} actual linear-regexp result, capture and syntax checks`);
