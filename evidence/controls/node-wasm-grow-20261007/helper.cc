// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
bool BackingStore::has_guard_regions() const {return guards;}
bool BackingStore::is_resizable_by_js() const {return resizable;}
bool JSArrayBuffer::is_shared() const {return shared;}
bool JSArrayBuffer::is_resizable_by_js() const {return resizable;}
size_t JSArrayBuffer::GetByteLength() const {return bytes;}
std::optional<size_t> BackingStore::GrowWasmMemoryInPlace(Isolate*,uint32_t amount,size_t maximum) {
 ++grows;
 if(fail || before>maximum-pages || amount>maximum-pages-before) {return std::nullopt;}
 size_t synchronized=pages+before;pages=synchronized+amount;return synchronized;
}
void BackingStore::BroadcastSharedWasmMemoryGrow(Isolate*) {
 ++broadcasts;pages+=after;
 auto* old=owner->array_buffer();require(old->shared);
 if(old->resizable) {old->bytes=pages*wasm::kWasmPageSize;}
 else {
  auto replacement=std::make_unique<JSArrayBuffer>(JSArrayBuffer{true,false,pages*wasm::kWasmPageSize,old->backing});
  owner->retired.push_back(std::move(owner->buffer));owner->buffer=std::move(replacement);
 }
}
