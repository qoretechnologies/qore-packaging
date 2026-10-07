// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Entire unchanged/fixed upstream candidate selection method, typed heap adapters.
#include <algorithm>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <numeric>
#include <string>
#include <vector>
#define require(value) do { if (!(value)) { std::fprintf(stderr,"check failed line %d: %s\n",__LINE__,#value);std::abort(); } } while(false)
#define CHECK(c) require(c)
#define CHECK_NULL(c) require((c)==nullptr)
#ifdef DEBUG
#define DCHECK(c) require(c)
#define DCHECK_GE(a,b) require((a)>=(b))
#define DCHECK_LE(a,b) require((a)<=(b))
#else
#define DCHECK(c) ((void)0)
#define DCHECK_GE(a,b) ((void)0)
#define DCHECK_LE(a,b) ((void)0)
#endif
constexpr size_t KB=1024;
enum Space { OLD_SPACE, CODE_SPACE, SHARED_SPACE, TRUSTED_SPACE };
const char* ToString(Space value) { return value==OLD_SPACE?"old":value==CODE_SPACE?"code":value==SHARED_SPACE?"shared":"trusted"; }
struct Flags { bool manual_evacuation_candidates_selection=false; bool stress_compaction_random=false; bool stress_compaction=false; bool compact_on_every_full_gc=false; bool trace_fragmentation_verbose=false; bool trace_fragmentation=false; } v8_flags;
std::vector<std::string> output;
struct Random { double NextDouble() { return 0.5; } std::vector<uint64_t> NextSample(size_t length,size_t n) { require(n<=length);std::vector<uint64_t> r(n);std::iota(r.begin(),r.end(),0);return r; } };
struct Isolate { Random random; Random* fuzzer_rng() { return &random; } };
struct Heap { Isolate instance; bool reduce=false; Isolate* isolate() { return &instance; } bool ShouldReduceMemory() { return reduce; } };
struct Sweeper { bool sweeping_in_progress() { return false; } };
void PrintIsolate(Isolate*, const char* format, ...) {
 char text[1024];va_list ap;va_start(ap,format);int n=vsnprintf(text,sizeof(text),format,ap);va_end(ap);require(n>=0 && size_t(n)<sizeof(text));output.emplace_back(text);
}
enum Slots { OLD_TO_OLD };
struct MemoryChunk {
 enum Flag { FORCE_EVACUATION_CANDIDATE_FOR_TESTING };
 bool never=false,allocatable=true,pinned=false,forced=false,candidate=false;
 bool NeverEvacuate() { return never; } bool CanAllocate() { return allocatable; } bool IsPinned() { return pinned; }
 bool IsFlagSet(Flag) { return forced; } void ClearFlagSlow(Flag) { forced=false; } bool IsEvacuationCandidate() { return candidate; }
};
struct PageMetadata {
 MemoryChunk chunk; size_t live,capacity; unsigned id;
 PageMetadata(size_t bytes,size_t area,unsigned i):live(bytes),capacity(area),id(i) {}
 MemoryChunk* Chunk() { return &chunk; }
 template<Slots> void* slot_set() { return nullptr; } template<Slots> void* typed_slot_set() { return nullptr; }
 bool SweepingDone() { return true; } size_t area_size() { return capacity; } size_t allocated_bytes() { return live; }
};
struct PagedSpace {
 Space tag;size_t capacity;std::vector<PageMetadata*> pages;
 Space identity() { return tag; } int CountTotalPages() { return int(pages.size()); } size_t AreaSize() { return capacity; }
 auto begin() { return pages.begin(); } auto end() { return pages.end(); }
};
struct MarkCompactCollector {
 Heap* heap_;Sweeper* sweeper_;unsigned heuristic_calls=0;std::vector<unsigned> candidates;
 void ComputeEvacuationHeuristics(size_t,int* target,size_t* max) { ++heuristic_calls;*target=50;*max=64*KB; }
 void AddEvacuationCandidate(PageMetadata* page) { require(!page->chunk.candidate);page->chunk.candidate=true;candidates.push_back(page->id); }
 void CollectEvacuationCandidates(PagedSpace* space);
};
void MarkCompactCollector::CollectEvacuationCandidates(PagedSpace* space) {
  DCHECK(space->identity() == OLD_SPACE || space->identity() == CODE_SPACE ||
         space->identity() == SHARED_SPACE ||
         space->identity() == TRUSTED_SPACE);

  int number_of_pages = space->CountTotalPages();
  size_t area_size = space->AreaSize();

  const bool in_standard_path =
      !(v8_flags.manual_evacuation_candidates_selection ||
        v8_flags.stress_compaction_random || v8_flags.stress_compaction ||
        v8_flags.compact_on_every_full_gc);
  // Those variables will only be initialized if |in_standard_path|, and are not
  // used otherwise.
  size_t max_evacuated_bytes;
  int target_fragmentation_percent;
  size_t free_bytes_threshold;
  if (in_standard_path) {
    // We use two conditions to decide whether a page qualifies as an evacuation
    // candidate, or not:
    // * Target fragmentation: How fragmented is a page, i.e., how is the ratio
    //   between live bytes and capacity of this page (= area).
    // * Evacuation quota: A global quota determining how much bytes should be
    //   compacted.
    ComputeEvacuationHeuristics(area_size, &target_fragmentation_percent,
                                &max_evacuated_bytes);
    free_bytes_threshold = target_fragmentation_percent * (area_size / 100);
  }

  // Pairs of (live_bytes_in_page, page).
  using LiveBytesPagePair = std::pair<size_t, PageMetadata*>;
  std::vector<LiveBytesPagePair> pages;
  pages.reserve(number_of_pages);

  DCHECK(!sweeper_->sweeping_in_progress());
  for (PageMetadata* p : *space) {
    MemoryChunk* chunk = p->Chunk();
    if (chunk->NeverEvacuate() || !chunk->CanAllocate()) continue;

    if (chunk->IsPinned()) {
      DCHECK(!chunk->IsFlagSet(
          MemoryChunk::FORCE_EVACUATION_CANDIDATE_FOR_TESTING));
      continue;
    }

    // Invariant: Evacuation candidates are just created when marking is
    // started. This means that sweeping has finished. Furthermore, at the end
    // of a GC all evacuation candidates are cleared and their slot buffers are
    // released.
    CHECK(!chunk->IsEvacuationCandidate());
    CHECK_NULL(p->slot_set<OLD_TO_OLD>());
    CHECK_NULL(p->typed_slot_set<OLD_TO_OLD>());
    CHECK(p->SweepingDone());
    DCHECK(p->area_size() == area_size);
    if (in_standard_path) {
      // Only the pages with at more than |free_bytes_threshold| free bytes are
      // considered for evacuation.
      if (area_size - p->allocated_bytes() >= free_bytes_threshold) {
        pages.push_back(std::make_pair(p->allocated_bytes(), p));
      }
    } else {
      pages.push_back(std::make_pair(p->allocated_bytes(), p));
    }
  }

  int candidate_count = 0;
  size_t total_live_bytes = 0;

  const bool reduce_memory = heap_->ShouldReduceMemory();
  if (v8_flags.manual_evacuation_candidates_selection) {
    for (size_t i = 0; i < pages.size(); i++) {
      PageMetadata* p = pages[i].second;
      MemoryChunk* chunk = p->Chunk();
      if (chunk->IsFlagSet(
              MemoryChunk::FORCE_EVACUATION_CANDIDATE_FOR_TESTING)) {
        candidate_count++;
        total_live_bytes += pages[i].first;
        chunk->ClearFlagSlow(
            MemoryChunk::FORCE_EVACUATION_CANDIDATE_FOR_TESTING);
        AddEvacuationCandidate(p);
      }
    }
  } else if (v8_flags.stress_compaction_random) {
    double fraction = heap_->isolate()->fuzzer_rng()->NextDouble();
    size_t pages_to_mark_count =
        static_cast<size_t>(fraction * (pages.size() + 1));
    for (uint64_t i : heap_->isolate()->fuzzer_rng()->NextSample(
             pages.size(), pages_to_mark_count)) {
      candidate_count++;
      total_live_bytes += pages[i].first;
      AddEvacuationCandidate(pages[i].second);
    }
  } else if (v8_flags.stress_compaction) {
    for (size_t i = 0; i < pages.size(); i++) {
      PageMetadata* p = pages[i].second;
      if (i % 2 == 0) {
        candidate_count++;
        total_live_bytes += pages[i].first;
        AddEvacuationCandidate(p);
      }
    }
  } else {
    // The following approach determines the pages that should be evacuated.
    //
    // Sort pages from the most free to the least free, then select
    // the first n pages for evacuation such that:
    // - the total size of evacuated objects does not exceed the specified
    // limit.
    // - fragmentation of (n+1)-th page does not exceed the specified limit.
    std::sort(pages.begin(), pages.end(),
              [](const LiveBytesPagePair& a, const LiveBytesPagePair& b) {
                return a.first < b.first;
              });
    for (size_t i = 0; i < pages.size(); i++) {
      size_t live_bytes = pages[i].first;
      DCHECK_GE(area_size, live_bytes);
      if (v8_flags.compact_on_every_full_gc ||
          ((total_live_bytes + live_bytes) <= max_evacuated_bytes)) {
        candidate_count++;
        total_live_bytes += live_bytes;
      }
      if (v8_flags.trace_fragmentation_verbose) {
        PrintIsolate(heap_->isolate(),
                     "compaction-selection-page: space=%s free_bytes_page=%zu "
                     "fragmentation_limit_kb=%zu "
                     "fragmentation_limit_percent=%d sum_compaction_kb=%zu "
                     "compaction_limit_kb=%zu\n",
                     ToString(space->identity()), (area_size - live_bytes) / KB,
                     free_bytes_threshold / KB, target_fragmentation_percent,
                     total_live_bytes / KB, max_evacuated_bytes / KB);
      }
    }
    // How many pages we will allocated for the evacuated objects
    // in the worst case: ceil(total_live_bytes / area_size)
    int estimated_new_pages =
        static_cast<int>((total_live_bytes + area_size - 1) / area_size);
    DCHECK_LE(estimated_new_pages, candidate_count);
    int estimated_released_pages = candidate_count - estimated_new_pages;
    // Avoid (compact -> expand) cycles.
    if ((estimated_released_pages == 0) && !v8_flags.compact_on_every_full_gc) {
      candidate_count = 0;
    }
    for (int i = 0; i < candidate_count; i++) {
      AddEvacuationCandidate(pages[i].second);
    }
  }

  if (v8_flags.trace_fragmentation) {
    PrintIsolate(heap_->isolate(),
                 "compaction-selection: space=%s reduce_memory=%d pages=%d "
                 "total_live_bytes=%zu\n",
                 ToString(space->identity()), reduce_memory, candidate_count,
                 total_live_bytes / KB);
  }
}

int main(int argc,char**) {
 unsigned checks=0;const bool baseline=argc>1;
 for(unsigned repeat=0;repeat<(baseline?1:100);++repeat) {
  for(unsigned mode=0;mode<16;++mode) {
   for(bool trace:{false,true}) {
    for(Space tag:{OLD_SPACE,CODE_SPACE,SHARED_SPACE,TRUSTED_SPACE}) {
     for(unsigned count:{0u,1u,7u}) {
      v8_flags={bool(mode&1),bool(mode&2),bool(mode&4),bool(mode&8),trace,trace};output.clear();
      Heap heap;Sweeper sweeper;MarkCompactCollector collector{&heap,&sweeper,0,{}};
      PagedSpace space{tag,64*KB,{}};std::vector<PageMetadata> storage;storage.reserve(count);
      for(unsigned i=0;i<count;++i) {storage.emplace_back((i%4)*16*KB,space.capacity,i);space.pages.push_back(&storage.back());}
      if(count==7) { storage[4].chunk.pinned=true; storage[5].chunk.never=true; storage[6].chunk.allocatable=false; }
      for(unsigned i=0;i<count;++i) { if(!storage[i].chunk.pinned) { storage[i].chunk.forced=(i%2==0); } }
      collector.CollectEvacuationCandidates(&space);
      require(collector.heuristic_calls==(mode==0?1u:0u));
      unsigned eligible=count==7?4:count;
      if(mode&1) { require(collector.candidates.size()==(eligible+1)/2); }
      else if(mode&2) { require(collector.candidates.size()==size_t(0.5*(eligible+1))); }
      else if(mode&4) { require(collector.candidates.size()==(eligible+1)/2); }
      else if(mode&8) { require(collector.candidates.size()==eligible); }
      else { require(collector.candidates.size()==(count==7?3:count)); }
      unsigned per_page=0;
      for(const auto& line:output) {
       if(line.find("compaction-selection-page:")!=std::string::npos) {
        ++per_page;
        if(!baseline) {
         if(mode&8) {require(line.find("mode=compact-on-every-full-gc")!=std::string::npos);require(line.find("fragmentation_limit_")==std::string::npos);require(line.find("compaction_limit_")==std::string::npos);}
         else {require(line.find("fragmentation_limit_kb=31")!=std::string::npos);require(line.find("fragmentation_limit_percent=50")!=std::string::npos);require(line.find("compaction_limit_kb=64")!=std::string::npos);}
        }
       }
      }
      require(per_page==((trace && !(mode&7))?(mode==0?(count==7?3u:count):eligible):0u));
      ++checks;
     }
    }
   }
  }
 }
 std::printf("PASS: %u candidate selection/tracing combinations\n",checks);
}
