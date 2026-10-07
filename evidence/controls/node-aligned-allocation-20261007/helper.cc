// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
bool MainAllocator::EnsureAllocation(int size,AllocationAlignment alignment,AllocationOrigin) {
  if (ensure_fails) { return false; }
  auto base=reinterpret_cast<Address>(storage.data());
  area.top_=base+offset;
  // Model each reviewed policy's minimum capacity contract. Observer budgets
  // may shorten a LAB, but ComputeLimit clamps its capacity to the request.
  int needed=size+(semispace?Heap::GetFillToAlign(area.top_,alignment):Heap::GetMaximumFillToAlign(alignment));
  size_t capacity=policy_mode==0?size_t(needed):policy_mode==1?std::max(size_t(needed),size_t(64)):storage.size()-offset;
  require(capacity<=storage.size()-offset);area.limit_=area.top_+capacity;
  return true;
}
