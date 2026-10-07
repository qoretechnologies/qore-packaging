// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
int Heap::GetMaximumFillToAlign(AllocationAlignment alignment) {
  if (V8_COMPRESS_POINTERS_8GB_BOOL) return 0;
  switch (alignment) {
    case kTaggedAligned:
      return 0;
    case kDoubleAligned:
    case kDoubleUnaligned:
      return kDoubleSize - kTaggedSize;
    default:
      UNREACHABLE();
  }
}

// static
int Heap::GetFillToAlign(Address address, AllocationAlignment alignment) {
  if (V8_COMPRESS_POINTERS_8GB_BOOL) return 0;
  if (alignment == kDoubleAligned && (address & kDoubleAlignmentMask) != 0)
    return kTaggedSize;
  if (alignment == kDoubleUnaligned && (address & kDoubleAlignmentMask) == 0) {
    return kDoubleSize - kTaggedSize;  // No fill if double is always aligned.
  }
  return 0;
}

AllocationResult MainAllocator::AllocateFastAligned(
    int size_in_bytes, int* result_aligned_size_in_bytes,
    AllocationAlignment alignment, AllocationOrigin origin) {
  Address top = allocation_info().top();
  int filler_size = Heap::GetFillToAlign(top, alignment);
  int aligned_size_in_bytes = size_in_bytes + filler_size;

  if (!allocation_info().CanIncrementTop(aligned_size_in_bytes)) {
    return AllocationResult::Failure();
  }
  Tagged<HeapObject> obj = HeapObject::FromAddress(
      allocation_info().IncrementTop(aligned_size_in_bytes));
  if (result_aligned_size_in_bytes)
    *result_aligned_size_in_bytes = aligned_size_in_bytes;

  if (filler_size > 0) {
    obj = space_heap()->PrecedeWithFiller(obj, filler_size);
  }

  MSAN_ALLOCATED_UNINITIALIZED_MEMORY(obj.address(), size_in_bytes);

  DCHECK_IMPLIES(black_allocation_ == BlackAllocation::kAlwaysEnabled,
                 space_heap()->marking_state()->IsMarked(obj));

  return AllocationResult::FromObject(obj);
}

AllocationResult MainAllocator::AllocateRawSlowAligned(
    int size_in_bytes, AllocationAlignment alignment, AllocationOrigin origin) {
  if (!EnsureAllocation(size_in_bytes, alignment, origin)) {
    return AllocationResult::Failure();
  }

  int max_aligned_size = size_in_bytes + Heap::GetMaximumFillToAlign(alignment);
  int aligned_size_in_bytes;

  AllocationResult result = AllocateFastAligned(
      size_in_bytes, &aligned_size_in_bytes, alignment, origin);
  DCHECK_GE(max_aligned_size, aligned_size_in_bytes);
  DCHECK(!result.IsFailure());

  InvokeAllocationObservers(result.ToAddress(), size_in_bytes,
                            aligned_size_in_bytes, max_aligned_size);

  return result;
}

int main() {
  unsigned checks=0;
  for (unsigned repeat=0;repeat<100;++repeat) {
    for (int size:{kTaggedSize,16,64,256,4096}) {
      for (auto alignment:{kTaggedAligned,kDoubleAligned,kDoubleUnaligned}) {
        for (unsigned offset=0;offset<32;offset+=kTaggedSize) {
          for (auto origin:{AllocationOrigin::kRuntime,AllocationOrigin::kGC}) {
            for (bool semispace:{false,true}) {for (unsigned policy=0;policy<3;++policy) {
              for (bool fail:{false,true}) {
                MainAllocator a;a.offset=offset;a.semispace=semispace;a.policy_mode=policy;a.ensure_fails=fail;
                auto start=reinterpret_cast<Address>(a.storage.data())+offset;
                int fill=alignment==kTaggedAligned?0:alignment==kDoubleAligned?int((8-(start%8))%8):int(start%8==0?8-kTaggedSize:0);
                auto result=a.AllocateRawSlowAligned(size,alignment,origin);
                require(result.IsFailure()==fail);
                if (fail) {require(a.observations==0 && a.area.top()==0);}
                else {
                  require(result.ToAddress()==start+fill && a.area.top()==start+size+fill);
                  require(a.observations==1 && a.observed_address==start+fill && a.observed_size==size);
                  require(a.observed_aligned==size+fill && a.observed_max==size+(alignment==kTaggedAligned?0:8-kTaggedSize));
                  std::memset(reinterpret_cast<void*>(result.ToAddress()),0x5a,size);
                  for (int i=0;i<fill;++i) {require(a.storage[offset+i]==0xa5);}
                  require(a.storage[offset+fill]==0x5a && a.storage[offset+fill+size-1]==0x5a);
                }
                ++checks;
              }
            }}
          }
          // A direct fast-path failure must leave its output and top untouched.
          MainAllocator a;auto start=reinterpret_cast<Address>(a.storage.data())+offset;
          int needed=size+Heap::GetFillToAlign(start,alignment);a.area={start,start+needed-1};int output=-12345;
          require(a.AllocateFastAligned(size,&output,alignment,AllocationOrigin::kRuntime).IsFailure());
          require(output==-12345 && a.area.top()==start && a.observations==0);++checks;
          a.area.limit_=start+needed;
          require(!a.AllocateFastAligned(size,nullptr,alignment,AllocationOrigin::kRuntime).IsFailure());
          require(a.area.top()==start+needed);++checks;
        }
      }
    }
  }
  std::printf("PASS: %u aligned allocation, observer and failure checks, tagged size %d\n",checks,kTaggedSize);
}
