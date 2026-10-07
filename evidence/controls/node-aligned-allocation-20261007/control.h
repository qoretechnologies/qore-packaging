// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
inline void require(bool value) { if (!value) { std::abort(); } }
#ifdef DEBUG
#define DCHECK(x) require(bool(x))
#define DCHECK_GE(a,b) require((a)>=(b))
#define DCHECK_IMPLIES(a,b) require(!(a)||(b))
#else
#define DCHECK(x) ((void)0)
#define DCHECK_GE(a,b) ((void)0)
#define DCHECK_IMPLIES(a,b) ((void)0)
#endif
#define MSAN_ALLOCATED_UNINITIALIZED_MEMORY(a,b) ((void)0)
#define UNREACHABLE() std::abort()
using Address=uintptr_t;
constexpr int kTaggedSize=TEST_TAGGED_SIZE;
constexpr int kDoubleSize=8;
constexpr int kDoubleAlignmentMask=7;
constexpr bool V8_COMPRESS_POINTERS_8GB_BOOL=false;
enum AllocationAlignment { kTaggedAligned,kDoubleAligned,kDoubleUnaligned };
enum class AllocationOrigin { kRuntime,kGC };
enum class BlackAllocation { kDisabled,kAlwaysEnabled };
struct HeapObject {
  Address address_;
  Address address() const { return address_; }
  static HeapObject FromAddress(Address value) { return {value}; }
};
template<class T> using Tagged=T;
struct AllocationResult {
  Address address_;
  static AllocationResult Failure() { return {0}; }
  static AllocationResult FromObject(HeapObject object) { return {object.address()}; }
  bool IsFailure() const { return address_==0; }
  Address ToAddress() const { DCHECK(!IsFailure());return address_; }
};
struct Heap {
  static int GetMaximumFillToAlign(AllocationAlignment);
  static int GetFillToAlign(Address,AllocationAlignment);
  HeapObject PrecedeWithFiller(HeapObject object,int size) {
    std::memset(reinterpret_cast<void*>(object.address()),0xa5,size);
    return HeapObject::FromAddress(object.address()+size);
  }
  Heap* marking_state() { return this; }
  bool IsMarked(HeapObject) const { return true; }
};
struct Area {
  Address top_=0,limit_=0;
  Address top() const { return top_; }
  bool CanIncrementTop(size_t size) const { return size<=limit_-top_; }
  Address IncrementTop(size_t size) { require(CanIncrementTop(size));Address old=top_;top_+=size;return old; }
};
struct MainAllocator {
  alignas(16) std::array<unsigned char,16384> storage{};
  Heap heap;
  Area area;
  BlackAllocation black_allocation_=BlackAllocation::kDisabled;
  bool ensure_fails=false;
  bool semispace=false;
  unsigned policy_mode=0;
  unsigned offset=0;
  unsigned observations=0;
  Address observed_address=0;
  int observed_size=0,observed_aligned=0,observed_max=0;
  Area& allocation_info() { return area; }
  Heap* space_heap() { return &heap; }
  bool EnsureAllocation(int,AllocationAlignment,AllocationOrigin);
  AllocationResult AllocateFastAligned(int,int*,AllocationAlignment,AllocationOrigin);
  AllocationResult AllocateRawSlowAligned(int,AllocationAlignment,AllocationOrigin);
  void InvokeAllocationObservers(Address address,int size,int aligned,int maximum) {
    ++observations;observed_address=address;observed_size=size;observed_aligned=aligned;observed_max=maximum;
  }
};
