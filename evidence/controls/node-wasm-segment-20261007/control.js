// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
vm.runInThisContext(fs.readFileSync('/work/wasm-module-builder.js','utf8')+`
globalThis.makeSegmentModule = function(segments, invalidIndex) {
  const builder=new WasmModuleBuilder();
  const array=builder.addArray(kWasmI8,true);
  segments.forEach(bytes=>builder.addPassiveDataSegment(bytes));
  segments.forEach((bytes,index)=>{
    builder.addFunction('segment'+index,makeSig([kWasmI32,kWasmI32],[kWasmStringRef]))
      .addBody([
        ...wasmI32Const(0),...wasmI32Const(bytes.length),
        kGCPrefix,kExprArrayNewData,...wasmUnsignedLeb(array),...wasmUnsignedLeb(invalidIndex?segments.length:index),
        kExprLocalGet,0,kExprLocalGet,1,
        kGCPrefix,...wasmUnsignedLeb(kExprStringNewWtf8Array)
      ]).exportFunc();
  });
  return builder.instantiate();
};`,{filename:'wasm-module-builder-and-segment-fixture.js'});
const fixtures=[
  {bytes:[],text:''},
  {bytes:[97,98,99],text:'abc'},
  {bytes:[0,127],text:'\u0000\u007f'},
  {bytes:[0xc2,0xa3],text:'£'},
  {bytes:[0xf0,0x9f,0x98,0x80],text:'😀'},
  {bytes:[0xed,0xa0,0x80],text:'\ud800'},
  {bytes:[0x61,0xc2,0xa3,0x62],text:'a£b'},
  {bytes:[0x80],invalid:true},
];
let checks=0;
for(let repeat=0;repeat<20;++repeat) {
  const module=makeSegmentModule(fixtures.map(f=>f.bytes),false);
  for(let index=0;index<fixtures.length;++index) {
    const fixture=fixtures[index], f=module.exports['segment'+index];
    for(let run=0;run<20;++run) {
      if(fixture.invalid) {assert.throws(()=>f(0,fixture.bytes.length),WebAssembly.RuntimeError);}
      else {assert.equal(f(0,fixture.bytes.length),fixture.text);}
      assert.equal(f(0,0),'');
      assert.equal(f(fixture.bytes.length,fixture.bytes.length),'');
      assert.throws(()=>f(0,fixture.bytes.length+1),WebAssembly.RuntimeError);
      assert.throws(()=>f(-1,fixture.bytes.length),WebAssembly.RuntimeError);
      if(fixture.bytes.length) {assert.throws(()=>f(fixture.bytes.length,0),WebAssembly.RuntimeError);}
      checks+=fixture.bytes.length?6:5;
    }
  }
  assert.equal(module.exports.segment6(1,3),'£');++checks;
  assert.throws(()=>makeSegmentModule([[97]],true),WebAssembly.CompileError);++checks;
}
console.log(`PASS: ${checks} actual Wasm data-segment string, encoding and bounds checks`);
