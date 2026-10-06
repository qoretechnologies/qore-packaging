// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Unchanged V8 enum branches; observable allocator and error-reporting adapters.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <mutex>
#define CHECK_EQ(a,b) do { if ((a)!=(b)) { std::abort(); } } while(false)
#define DCHECK_EQ(a,b) CHECK_EQ(a,b)
#define DCHECK_NE(a,b) do { if ((a)==(b)) { std::abort(); } } while(false)
using Address = uintptr_t;
struct MutexGuard { std::lock_guard<std::mutex> guard; explicit MutexGuard(std::mutex* m):guard(*m) {} };
enum class PageInitializationMode {
  // The contents of allocated pages must be zero initialized. This causes any
  // committed pages to be decommitted during FreePages and ReleasePages.
  kAllocatedPagesMustBeZeroInitialized,
  // Allocated pages do not have to be be zero initialized and can contain old
  // data. This is slightly faster as comitted pages are not decommitted
  // during FreePages and ReleasePages, but only made inaccessible.
  kAllocatedPagesCanBeUninitialized,
  // Assume pages are in discarded state and already have the right page
  // permissions. Using this mode requires PageFreeingMode::kDiscard.
  kRecommitOnly,
};
enum class PageFreeingMode {
  // Pages are freed/released by setting permissions to kNoAccess. This is the
  // preferred mode when current platform/configuration allows any page
  // permissions reconfiguration.
  kMakeInaccessible,

  // Pages are freed/released by using DiscardSystemPages of the underlying
  // page allocator. This mode should be used for the cases when page permission
  // reconfiguration is not allowed. In particular, on MacOS on ARM64 ("Apple
  // M1"/Apple Silicon) it's not allowed to reconfigure RWX pages to anything
  // else.
  // This mode is not compatible with kAllocatedPagesMustBeZeroInitialized
  // page initialization mode.
  kDiscard,
};
struct PageAllocator {
 enum Permission { kNoAccess };
 int called=0; bool result=false;
 void* address=nullptr; size_t size=0;
 bool visit(int method,void* p,size_t n) { called=method; address=p; size=n; return result; }
 bool DecommitPages(void* p,size_t n) { return visit(1,p,n); }
 bool SetPermissions(void* p,size_t n,Permission permission) { CHECK_EQ(permission,kNoAccess); return visit(2,p,n); }
 bool DiscardSystemPages(void* p,size_t n) { return visit(3,p,n); }
};
struct RegionAllocator { unsigned calls=0; Address address=0; size_t FreeRegion(Address a) { ++calls;address=a;return 4096; } };
struct BoundedPageAllocator {
 PageAllocator* page_allocator_; PageInitializationMode page_initialization_mode_; PageFreeingMode page_freeing_mode_;
 std::mutex mutex_; RegionAllocator region_allocator_;
 __attribute__((noinline)) bool FreePages(void*,size_t);
};
bool BoundedPageAllocator::FreePages(void* raw_address, size_t size) {
  // Careful: we are not locked here, do not touch BoundedPageAllocator
  // metadata.
  bool success;
  Address address = reinterpret_cast<Address>(raw_address);

  // The operations below can be expensive, don't hold the lock while they
  // happen. There is still potentially contention in the kernel, but at least
  // we don't need to hold the V8-side lock.
  if (page_initialization_mode_ ==
      PageInitializationMode::kAllocatedPagesMustBeZeroInitialized) {
    DCHECK_NE(page_freeing_mode_, PageFreeingMode::kDiscard);
    // When we are required to return zero-initialized pages, we decommit the
    // pages here, which will cause any wired pages to be removed by the OS.
    success = page_allocator_->DecommitPages(raw_address, size);
  } else {
    switch (page_freeing_mode_) {
      case PageFreeingMode::kMakeInaccessible:
        DCHECK_EQ(page_initialization_mode_,
                  PageInitializationMode::kAllocatedPagesCanBeUninitialized);
        success = page_allocator_->SetPermissions(raw_address, size,
                                                  PageAllocator::kNoAccess);
        break;

      case PageFreeingMode::kDiscard:
        success = page_allocator_->DiscardSystemPages(raw_address, size);
        break;
    }
  }

  MutexGuard guard(&mutex_);
  CHECK_EQ(size, region_allocator_.FreeRegion(address));

  return success;
}

enum class FieldSynchronization {
  kNone,
  kRelaxed,
  kAcquireRelease,
};
struct Field { FieldSynchronization synchronization; };
struct Diagnostic { const char* message; };
[[noreturn]] void ReportError(const char* text) { throw Diagnostic{text}; }
__attribute__((noinline)) const char* load_plain(Field class_field) {
const char* load;
    switch (class_field.synchronization) {
      case FieldSynchronization::kNone:
        load = "ReadField";
        break;
      case FieldSynchronization::kRelaxed:
        load = "Relaxed_ReadField";
        break;
      case FieldSynchronization::kAcquireRelease:
        ReportError("Torque doesn't support @cppAcquireLoad on untagged data");
    }
return load;
}
__attribute__((noinline)) const char* load_tagged(Field class_field) {
const char* load;
    switch (class_field.synchronization) {
      case FieldSynchronization::kNone:
        load = "load";
        break;
      case FieldSynchronization::kRelaxed:
        load = "Relaxed_Load";
        break;
      case FieldSynchronization::kAcquireRelease:
        load = "Acquire_Load";
        break;
    }
return load;
}
__attribute__((noinline)) const char* store_plain(Field class_field) {
const char* store;
    switch (class_field.synchronization) {
      case FieldSynchronization::kNone:
        store = "WriteField";
        break;
      case FieldSynchronization::kRelaxed:
        store = "Relaxed_WriteField";
        break;
      case FieldSynchronization::kAcquireRelease:
        ReportError("Torque doesn't support @cppReleaseStore on untagged data");
    }
return store;
}
__attribute__((noinline)) const char* write_macro(Field class_field, bool strong_pointer) {
    const char* write_macro;
    if (!strong_pointer) {
      if (class_field.synchronization ==
          FieldSynchronization::kAcquireRelease) {
        ReportError("Torque doesn't support @cppReleaseStore on weak fields");
      }
      write_macro = "RELAXED_WRITE_WEAK_FIELD";
    } else {
      switch (class_field.synchronization) {
        case FieldSynchronization::kNone:
          write_macro = "WRITE_FIELD";
          break;
        case FieldSynchronization::kRelaxed:
          write_macro = "RELAXED_WRITE_FIELD";
          break;
        case FieldSynchronization::kAcquireRelease:
          write_macro = "RELEASE_WRITE_FIELD";
          break;
      }
    }
return write_macro;
}

int main() {
 unsigned checks=0; char address;
 using I=PageInitializationMode; using F=PageFreeingMode; using S=FieldSynchronization;
 struct Mode { I init;F free;int call; };
 const Mode modes[]={{I::kAllocatedPagesMustBeZeroInitialized,F::kMakeInaccessible,1},{I::kAllocatedPagesCanBeUninitialized,F::kMakeInaccessible,2},{I::kAllocatedPagesCanBeUninitialized,F::kDiscard,3},{I::kRecommitOnly,F::kDiscard,3}};
 const S syncs[]={S::kNone,S::kRelaxed,S::kAcquireRelease};
 const char* plain_load[]={"ReadField","Relaxed_ReadField",nullptr};
 const char* tagged_load[]={"load","Relaxed_Load","Acquire_Load"};
 const char* plain_store[]={"WriteField","Relaxed_WriteField",nullptr};
 const char* strong_store[]={"WRITE_FIELD","RELAXED_WRITE_FIELD","RELEASE_WRITE_FIELD"};
 auto check=[&](auto fn,const char* expected) {
  try { const char* actual=fn(); if (!expected || std::strcmp(actual,expected)) { std::abort(); } }
  catch(const Diagnostic& diagnostic) { if(expected || !diagnostic.message || !*diagnostic.message) { std::abort(); } }
  ++checks;
 };
 for(unsigned n=0;n<10000;++n) {
  for(const Mode& mode:modes) {
   for(bool result:{false,true}) {
    PageAllocator page;page.result=result;BoundedPageAllocator allocator{&page,mode.init,mode.free,{}, {}};
    CHECK_EQ(allocator.FreePages(&address,4096),result);CHECK_EQ(page.called,mode.call);CHECK_EQ(page.address,&address);CHECK_EQ(page.size,4096u);CHECK_EQ(allocator.region_allocator_.calls,1u);CHECK_EQ(allocator.region_allocator_.address,reinterpret_cast<Address>(&address));++checks;
   }
  }
  for(unsigned i=0;i<3;++i) {
   Field field{syncs[i]};
   check([&]{return load_plain(field);},plain_load[i]);
   check([&]{return load_tagged(field);},tagged_load[i]);
   check([&]{return store_plain(field);},plain_store[i]);
   check([&]{return write_macro(field,true);},strong_store[i]);
   check([&]{return write_macro(field,false);},i<2?"RELAXED_WRITE_WEAK_FIELD":nullptr);
  }
 }
 std::printf("%u allocator/field-mode checks passed\n",checks);
}
