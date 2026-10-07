// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert=require('node:assert/strict');
const {Worker,isMainThread,parentPort,workerData}=require('node:worker_threads');
if(!isMainThread) {
  const {memory,count}=workerData;
  parentPort.once('message',()=>{
    const results=[];
    for(let i=0;i<count;++i) {
      results.push(memory.grow(1));
      assert.equal(new Uint8Array(memory.buffer)[0],137);
    }
    parentPort.postMessage(results);
  });
  parentPort.postMessage('ready');
} else {
  (async()=>{
    let checks=0;
    for(let repeat=0;repeat<5;++repeat) {
      for(const workers of [1,2,4]) {
        const count=16;
        const memory=new WebAssembly.Memory({initial:1,maximum:1+workers*count,shared:true});
        new Uint8Array(memory.buffer)[0]=137;
        const entries=[];
        try {
          for(let i=0;i<workers;++i) {
            const worker=new Worker(__filename,{workerData:{memory,count}});
            const ready=new Promise((resolve,reject)=>{
              worker.once('message',value=>{try {assert.equal(value,'ready');resolve();} catch(error) {reject(error);}});
              worker.once('error',reject);
            });
            entries.push({worker,ready});
          }
          await Promise.all(entries.map(entry=>entry.ready));
          const values=entries.map(({worker})=>new Promise((resolve,reject)=>{
            worker.once('message',resolve);worker.once('error',reject);
            worker.postMessage('grow');
          }));
          const actual=(await Promise.all(values)).flat().sort((a,b)=>a-b);
          assert.deepStrictEqual(actual,Array.from({length:workers*count},(_,i)=>i+1));
          assert.equal(memory.buffer.byteLength,(1+workers*count)*65536);
          assert.equal(memory.grow(0),1+workers*count);
          assert.throws(()=>memory.grow(1),RangeError);
          assert.equal(new Uint8Array(memory.buffer)[0],137);
          checks+=workers*count+4;
        } finally {
          await Promise.all(entries.map(({worker})=>worker.terminate()));
        }
      }
      const memory=new WebAssembly.Memory({initial:1,maximum:3});
      const old=memory.buffer;
      assert.equal(memory.grow(1),1);assert.equal(old.byteLength,0);
      assert.equal(memory.grow(1),2);assert.throws(()=>memory.grow(1),RangeError);
      checks+=4;
    }
    console.log(`PASS: ${checks} actual shared-worker and unshared Wasm growth checks`);
  })().catch(error=>{console.error(error);process.exitCode=1;});
}
