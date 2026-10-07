# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib, json, shutil
root=Path('work/node-obs-diagnostic-20261006/node-v24.18.1');out=Path('work/node-wasm-grow-controls-20261007');out.mkdir()
path='deps/v8/src/wasm/wasm-objects.cc';s=(root/path).read_text();a=s.index('int32_t WasmMemoryObject::Grow(');b=s.index('\n  size_t new_pages = old_pages + pages;',a);body=s[a:b]
(out/'source-extracts.json').write_text(json.dumps([dict(file=path,line=s[:a].count('\n')+1,body=body,sha256=hashlib.sha256(body.encode()).hexdigest())],indent=2)+'\n')
(out/'control.h').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <optional>
#include <vector>
inline void require(bool v) {if(!v) {std::abort();}}
#define CHECK_NE(a,b) require((a)!=(b))
#define CHECK_LE(a,b) require((a)<=(b))
#ifdef DEBUG
#define DCHECK_NOT_NULL(x) require(bool(x))
#define DCHECK_EQ(a,b) require((a)==(b))
#define DCHECK_GE(a,b) require((a)>=(b))
#define DCHECK(x) require(x)
#else
#define DCHECK_NOT_NULL(x) ((void)0)
#define DCHECK_EQ(a,b) ((void)0)
#define DCHECK_GE(a,b) ((void)0)
#define DCHECK(x) ((void)0)
#endif
#define TRACE_EVENT0(a,b) ((void)0)
#define FATAL(message) std::abort()
struct Isolate {};
template<class T> struct DirectHandle {
 T* ptr;
 DirectHandle(T* value,Isolate* = nullptr):ptr(value) {}
 T* operator->() const {return ptr;}
 T* operator*() const {return ptr;}
};
namespace wasm {
constexpr size_t kWasmPageSize=65536;
inline size_t max_mem32_pages() {return 65536;}
inline size_t max_mem64_pages() {return 1048576;}
}
struct Flags {bool stress_wasm_memory_moving=false;bool correctness_fuzzer_suppressions=false;};
extern Flags v8_flags;
struct WasmMemoryObject;
struct BackingStore {
 const bool guards;const bool resizable;const bool fail;
 size_t pages;const size_t before;const size_t after;
 unsigned grows=0;unsigned broadcasts=0;WasmMemoryObject* owner=nullptr;
 bool has_guard_regions() const;
 bool is_resizable_by_js() const;
 std::optional<size_t> GrowWasmMemoryInPlace(Isolate*,uint32_t amount,size_t maximum);
 void BroadcastSharedWasmMemoryGrow(Isolate*);
};
struct JSArrayBuffer {
 const bool shared;const bool resizable;
 size_t bytes;std::shared_ptr<BackingStore> backing;
 bool is_shared() const;
 bool is_resizable_by_js() const;
 size_t GetByteLength() const;
 std::shared_ptr<BackingStore> GetBackingStore() {return backing;}
};
struct WasmMemoryObject {
 const bool memory64;const bool bounded;const size_t maximum;
 std::unique_ptr<JSArrayBuffer> buffer;
 std::vector<std::unique_ptr<JSArrayBuffer>> retired;
 JSArrayBuffer* array_buffer() {return buffer.get();}
 bool is_memory64() const {return memory64;}
 bool has_maximum_pages() const {return bounded;}
 size_t maximum_pages() const {return maximum;}
 static int32_t Grow(Isolate*,DirectHandle<WasmMemoryObject>,uint32_t);
};
''')
(out/'helper.cc').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
''')
(out/'control.cc').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
Flags v8_flags{};
'''+body+r'''
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
''')
shutil.copy2(root/'deps/v8/LICENSE',out/'V8-LICENSE')
s=Path('work/node-deopt-scan-controls-20261007/run.py').read_text();(out/'run.py').write_text(s)
print('Prepared unchanged growth prefix through the shared-memory return.')
