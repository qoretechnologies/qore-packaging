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
