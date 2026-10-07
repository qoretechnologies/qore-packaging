// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert = require('node:assert/strict');
const body = `let total=0;
  for(let i=0;i<4;++i) {
    for(let j=0;j<5;++j) {
      for(let k=0;k<3;++k) {
        total+=(i+1)*(j+1)*(k+1)*values[(i+j+k)%values.length];
      }
    }
  }
  return total;`;
// Independent coefficient convolution for the weighted nested-loop result.
let coefficients=[1];
for(const size of [4,5,3]) {
  const next=Array(coefficients.length+size-1).fill(0);
  coefficients.forEach((value,index)=>{
    for(let i=0;i<size;++i) {next[index+i]+=value*(i+1);}
  });
  coefficients=next;
}
let checks=0;
for(let repeat=0;repeat<50;++repeat) {
  for(const length of [1,2,5]) {
    for(const kind of ['double','object','throw']) {
      const f=new Function('values',body);
      %PrepareFunctionForOptimization(f);
      const warm=Array.from({length},(_,i)=>i+1);
      for(let i=0;i<20;++i) {f(warm);}
      %OptimizeFunctionOnNextCall(f);
      f(warm);
      assert.ok(%GetOptimizationStatus(f)&16);
      const numbers=Array.from({length},(_,i)=>(i+1)/2);
      let calls=0;
      const error=new Error('deliberate conversion failure');
      const values=kind==='double'?numbers:numbers.map(value=>({valueOf(){
        ++calls;if(kind==='throw' && calls===17) {throw error;}return value;
      }}));
      if(kind==='throw') {
        assert.throws(()=>f(values), e=>e===error);assert.equal(calls,17);
      } else {
        assert.equal(f(values),coefficients.reduce((sum,weight,index)=>sum+weight*numbers[index%length],0));
        if(kind==='object') {assert.equal(calls,60);}
      }
      assert.equal(f(warm),coefficients.reduce((sum,weight,index)=>sum+weight*warm[index%length],0));
      ++checks;
    }
  }
}
console.log(`PASS: ${checks} actual optimized nested-loop deoptimization and recovery cases`);
