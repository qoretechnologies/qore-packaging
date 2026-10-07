// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
