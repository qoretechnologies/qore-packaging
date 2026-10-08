// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
globalThis.laneAssert = require('node:assert/strict');
const builder = fs.readFileSync(process.argv[2], 'utf8');
vm.runInThisContext(builder + `
const laneCases = [
  [kExprI8x16ExtractLaneS, 16, kWasmI32, (d, i) => d.getInt8(i)],
  [kExprI8x16ExtractLaneU, 16, kWasmI32, (d, i) => d.getUint8(i)],
  [kExprI16x8ExtractLaneS, 8, kWasmI32, (d, i) => d.getInt16(i * 2, true)],
  [kExprI16x8ExtractLaneU, 8, kWasmI32, (d, i) => d.getUint16(i * 2, true)],
  [kExprI32x4ExtractLane, 4, kWasmI32, (d, i) => d.getInt32(i * 4, true)],
  [kExprI64x2ExtractLane, 2, kWasmI64, (d, i) => d.getBigInt64(i * 8, true)],
  [kExprF16x8ExtractLane, 8, kWasmF32, (d, i) => half(d.getUint16(i * 2, true))],
  [kExprF32x4ExtractLane, 4, kWasmF32, (d, i) => d.getFloat32(i * 4, true)],
  [kExprF64x2ExtractLane, 2, kWasmF64, (d, i) => d.getFloat64(i * 8, true)],
];
function half(bits) {
  const sign = bits & 0x8000 ? -1 : 1;
  const exponent = (bits >> 10) & 31;
  const fraction = bits & 1023;
  if (exponent === 31) return fraction ? NaN : sign * Infinity;
  if (exponent === 0) return sign * fraction * 2 ** -24;
  return sign * (1 + fraction / 1024) * 2 ** (exponent - 15);
}
function laneBody(opcode, lane) {
  return [kExprI32Const, 0, kSimdPrefix, kExprS128LoadMem, 0, 0,
          kSimdPrefix, ...(Array.isArray(opcode) ? opcode : [opcode]), lane];
}
const mod = new WasmModuleBuilder();
mod.addMemory(1, 1);
mod.exportMemoryAs('memory');
for (let kind = 0; kind < laneCases.length; ++kind) {
  const [opcode, lanes, result] = laneCases[kind];
  for (let lane = 0; lane < lanes; ++lane) {
    mod.addFunction('lane_' + kind + '_' + lane, makeSig([], [result]))
       .addBody(laneBody(opcode, lane)).exportFunc();
  }
}
const instance = mod.instantiate();
const data = new Uint8Array(instance.exports.memory.buffer);
const view = new DataView(data.buffer);
const patterns = [
  Array(16).fill(0), Array(16).fill(255),
  Array.from({length:16}, (_, i) => i * 17),
  Array.from({length:16}, (_, i) => i % 2 ? 128 : 0),
  Array.from({length:16}, (_, i) => i % 2 ? 124 : 0),
  Array.from({length:16}, (_, i) => (i * 73 + 19) & 255),
];
let checks = 0;
for (const pattern of patterns) {
  data.set(pattern);
  for (let kind = 0; kind < laneCases.length; ++kind) {
    const [, lanes, , expected] = laneCases[kind];
    for (let lane = 0; lane < lanes; ++lane) {
      laneAssert.equal(instance.exports['lane_' + kind + '_' + lane](), expected(view, lane));
      ++checks;
    }
  }
}
for (const [opcode, lanes, result] of laneCases) {
  for (const invalid of [lanes, 255]) {
    const bad = new WasmModuleBuilder();
    bad.addMemory(1, 1);
    bad.addFunction('bad', makeSig([], [result])).addBody(laneBody(opcode, invalid)).exportFunc();
    laneAssert.throws(() => bad.toModule(), WebAssembly.CompileError);
    ++checks;
  }
}
console.log(JSON.stringify({node:process.version, arch:process.arch, kinds:laneCases.length, checks, result:'pass'}));
`);
