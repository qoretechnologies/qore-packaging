# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib,hashlib,json,shutil,subprocess
root=Path.cwd();src=root/'work/node-obs-diagnostic-20261006/node-v24.18.1';out=root/'work/node-compaction-trace-fix4-20261006';out.mkdir()
path='deps/v8/src/heap/mark-compact.cc';s=(src/path).read_text();a=s.index('void MarkCompactCollector::CollectEvacuationCandidates(');b=s.index('\nvoid MarkCompactCollector::Prepare()',a);body=s[a:b]
old='''      if (v8_flags.trace_fragmentation_verbose) {
        PrintIsolate(heap_->isolate(),
'''
new='''      if (v8_flags.trace_fragmentation_verbose && !in_standard_path) {
        // Forced compaction does not compute or apply fragmentation thresholds.
        PrintIsolate(heap_->isolate(),
                     "compaction-selection-page: space=%s free_bytes_page=%zu "
                     "mode=compact-on-every-full-gc sum_compaction_kb=%zu\\n",
                     ToString(space->identity()), (area_size - live_bytes) / KB,
                     total_live_bytes / KB);
      } else if (v8_flags.trace_fragmentation_verbose) {
        PrintIsolate(heap_->isolate(),
'''
assert body.count(old)==1;fixedbody=body.replace(old,new);fixed=s[:a]+fixedbody+s[b:]
(out/'original-method.cc').write_text(body);(out/'fixed-method.cc').write_text(fixedbody)
patch='# Copyright 2026 Qore Technologies, s.r.o.; BSD-3-Clause.\n# Do not read unused heuristic thresholds when tracing forced full compaction.\n'+''.join(difflib.unified_diff(s.splitlines(True),fixed.splitlines(True),fromfile='a/'+path,tofile='b/'+path))
(out/'nodejs24-compaction-trace.patch').write_text(patch);shutil.copy2(src/'deps/v8/LICENSE',out/'V8-LICENSE')
header=r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
'''
tests=r'''
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
'''
(out/'header.cc').write_text(header);(out/'tests.cc').write_text(tests)
for name,method in [('original',body),('fixed',fixedbody)]:(out/(name+'.cc')).write_text(header+method+tests)
runner='''# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
out=Path('/work');records=[]
for name,mode in [('original','debug'),('fixed','debug'),('fixed','release')]:
 stem=name+'-'+mode
 commands=[['g++','-std=c++20','-g','-O0' if mode=='debug' else '-O2','-Wall','-Wextra']+(['-DDEBUG'] if mode=='debug' else [])+['/work/'+name+'.cc','-o','/work/'+stem],['/work/'+stem]+(['baseline'] if name=='original' else []),['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/work/'+stem+'-valgrind.log','/work/'+stem]+(['baseline'] if name=='original' else [])]
 for phase,cmd in zip(('compile','normal','memory'),commands):
  with (out/(stem+'-'+phase+'.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
  records.append({'name':stem+'-'+phase,'command':cmd,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(records,indent=2)+'\\n')
  if not(name=='original' and phase=='memory'):r.check_returncode()
  elif r.returncode!=99:raise AssertionError(('baseline did not expose uninitialized trace',r.returncode))
'''
(out/'run.py').write_text(runner);(out/'source.json').write_text(json.dumps({'path':path,'sha256':hashlib.sha256(s.encode()).hexdigest(),'line':s[:a].count('\n')+1,'root_cause':'compact_on_every_full_gc bypasses heuristic initialization but reaches unconditional verbose trace formatting of three heuristic fields.'},indent=2)+'\n')
cmd=['docker','run','--rm','--init','--network','none','--user','1019:100','-v',str(out)+':/work','sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414','python3','-B','-W','error','/work/run.py'];(out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (out/'run.log').open('x') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
