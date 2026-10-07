// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
Flags v8_flags{};
int32_t WasmMemoryObject::Grow(Isolate* isolate,
                               DirectHandle<WasmMemoryObject> memory_object,
                               uint32_t pages) {
  TRACE_EVENT0("v8.wasm", "wasm.GrowMemory");
  DirectHandle<JSArrayBuffer> old_buffer(memory_object->array_buffer(),
                                         isolate);

  std::shared_ptr<BackingStore> backing_store = old_buffer->GetBackingStore();
  // Wasm memory can grow, and Wasm memory always has a backing store.
  DCHECK_NOT_NULL(backing_store);

  // Check for maximum memory size.
  // Note: The {wasm::max_mem_pages()} limit is already checked in
  // {BackingStore::CopyWasmMemory}, and is irrelevant for
  // {GrowWasmMemoryInPlace} because memory is never allocated with more
  // capacity than that limit.
  size_t old_size = old_buffer->GetByteLength();
  DCHECK_EQ(0, old_size % wasm::kWasmPageSize);
  size_t old_pages = old_size / wasm::kWasmPageSize;
  size_t max_pages = memory_object->is_memory64() ? wasm::max_mem64_pages()
                                                  : wasm::max_mem32_pages();
  if (memory_object->has_maximum_pages()) {
    max_pages = std::min(max_pages,
                         static_cast<size_t>(memory_object->maximum_pages()));
  }
  DCHECK_GE(max_pages, old_pages);
  if (pages > max_pages - old_pages) return -1;

  const bool must_grow_in_place = old_buffer->is_shared() ||
                                  backing_store->has_guard_regions() ||
                                  backing_store->is_resizable_by_js();
  const bool try_grow_in_place =
      must_grow_in_place || !v8_flags.stress_wasm_memory_moving;

  std::optional<size_t> result_inplace =
      try_grow_in_place
          ? backing_store->GrowWasmMemoryInPlace(isolate, pages, max_pages)
          : std::nullopt;
  if (must_grow_in_place && !result_inplace.has_value()) {
    // There are different limits per platform, thus crash if the correctness
    // fuzzer is running.
    if (v8_flags.correctness_fuzzer_suppressions) {
      FATAL("could not grow wasm memory");
    }
    return -1;
  }

  // Handle shared memory first.
  if (old_buffer->is_shared()) {
    DCHECK(result_inplace.has_value());
    backing_store->BroadcastSharedWasmMemoryGrow(isolate);
    if (!old_buffer->is_resizable_by_js()) {
      // Broadcasting the update should update this memory object too.
      CHECK_NE(*old_buffer, memory_object->array_buffer());
    }
    size_t new_pages = result_inplace.value() + pages;
    // If the allocation succeeded, then this can't possibly overflow:
    size_t new_byte_length = new_pages * wasm::kWasmPageSize;
    // This is a less than check, as it is not guaranteed that the SAB
    // length here will be equal to the stashed length above as calls to
    // grow the same memory object can come in from different workers.
    // It is also possible that a call to Grow was in progress when
    // handling this call.
    CHECK_LE(new_byte_length, memory_object->array_buffer()->GetByteLength());
    // As {old_pages} was read racefully, we return here the synchronized
    // value provided by {GrowWasmMemoryInPlace}, to provide the atomic
    // read-modify-write behavior required by the spec.
    return static_cast<int32_t>(result_inplace.value());  // success
  }

  // The copied prefix ends at the complete shared-memory return. This marker
  // identifies continuation into the unshared path; it is not a Grow result.
  return -2;
}
int main() {
 unsigned checks=0;
 for(unsigned repeat=0;repeat<10;++repeat) {
  for(bool memory64:{false,true}) {for(bool bounded:{false,true}) {
   for(size_t old:{size_t(0),size_t(1),size_t(4),size_t(65528)}) {
    for(uint32_t amount:{uint32_t(0),uint32_t(1),uint32_t(8),uint32_t(9),UINT32_MAX}) {
     for(unsigned flags=0;flags<8;++flags) {
      bool shared=flags&1,guards=flags&2,resizable=flags&4;
      for(bool stress:{false,true}) {for(bool fail:{false,true}) {
       for(size_t before:{size_t(0),size_t(2)}) {for(size_t after:{size_t(0),size_t(3)}) {
        if(!shared && (before || after)) {continue;}
        size_t maximum=bounded?old+8:(memory64?1048576:65536);
        // The modeled concurrent grow itself must fit the memory's maximum.
        if(before+amount+after>maximum-old && after) {continue;}
        auto store=std::make_shared<BackingStore>(BackingStore{guards,resizable,fail,old,before,after});
        WasmMemoryObject object{memory64,bounded,old+8,
          std::make_unique<JSArrayBuffer>(JSArrayBuffer{shared,resizable,old*wasm::kWasmPageSize,store}),{}};
        store->owner=&object;v8_flags.stress_wasm_memory_moving=stress;Isolate isolate;
        int32_t result=WasmMemoryObject::Grow(&isolate,&object,amount);
        bool overflow=amount>maximum-old;
        bool must=shared||guards||resizable;
        bool attempt=!overflow && (must||!stress);
        bool success=attempt && !fail && amount<=maximum-old-before;
        int32_t expected=overflow||(must&&!success)?-1:(shared?static_cast<int32_t>(old+before):-2);
        require(result==expected && store->grows==unsigned(attempt));
        require(store->broadcasts==unsigned(shared&&success));
        if(shared&&success) {
         require(object.buffer->bytes==(old+before+amount+after)*wasm::kWasmPageSize);
         require(object.retired.size()==size_t(!resizable));
        }
        ++checks;
       }}
      }}
     }
    }
   }
  }}
 }
 std::printf("PASS: %u Wasm growth guard, failure and synchronized-result checks\n",checks);
}
