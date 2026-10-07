# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib, json, shutil
root=Path('work/node-obs-diagnostic-20261006/node-v24.18.1')
out=Path('work/node-aligned-allocation-controls-20261007');out.mkdir()
extracts=[]
def extract(path, start, end):
    s=(root/path).read_text();a=s.index(start);b=s.index(end,a);body=s[a:b]
    extracts.append(dict(file=path,line=s[:a].count('\n')+1,body=body,sha256=hashlib.sha256(body.encode()).hexdigest()))
    return body
slow=extract('deps/v8/src/heap/main-allocator.cc','AllocationResult MainAllocator::AllocateRawSlowAligned(', '\nvoid MainAllocator::MakeLinearAllocationAreaIterable')
fast=extract('deps/v8/src/heap/main-allocator-inl.h','AllocationResult MainAllocator::AllocateFastAligned(', '\nbool MainAllocator::TryFreeLast')
align=extract('deps/v8/src/heap/heap.cc','int Heap::GetMaximumFillToAlign(', '\nsize_t Heap::GetCodeRangeReservedAreaSize')
for start,end in [('Address MainAllocator::ComputeLimit(', '\n#if DEBUG'),('bool SemiSpaceNewSpaceAllocatorPolicy::EnsureAllocation(', '\nvoid SemiSpaceNewSpaceAllocatorPolicy::FreeLinearAllocationArea'),('bool PagedSpaceAllocatorPolicy::EnsureAllocation(', '\nbool PagedSpaceAllocatorPolicy::RefillLab'),('bool PagedSpaceAllocatorPolicy::TryExtendLAB(', '\nvoid PagedSpaceAllocatorPolicy::FreeLinearAllocationArea')]:
    extract('deps/v8/src/heap/main-allocator.cc',start,end)
(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n')
(out/'control.h').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
''')
(out/'helper.cc').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
''')
(out/'control.cc').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
'''+align+'\n'+fast+'\n'+slow+r'''
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
''')
(out/'run.py').write_text('''# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
out=Path('/work');results=[]
for tagged in (4,8):
 for mode in ('release','debug'):
  name=mode+'-'+str(tagged)
  commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra','-Wno-unused-parameter','-DTEST_TAGGED_SIZE='+str(tagged)]+(['-DDEBUG'] if mode=='debug' else [])+['/work/control.cc','/work/helper.cc','-o','/work/control-'+name],['/work/control-'+name],['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/work/'+name+'-valgrind.log','/work/control-'+name]]
  for phase,command in zip(('compile','normal','memory'),commands):
   with (out/(name+'-'+phase+'.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
   results.append(dict(name=name+'-'+phase,command=command,exit_code=r.returncode));(out/'status.json').write_text(json.dumps(results,indent=2)+'\\n');r.check_returncode()
''')
shutil.copy2(root/'deps/v8/LICENSE',out/'V8-LICENSE')
print('Prepared exact aligned fast/slow paths and alignment helpers.')
