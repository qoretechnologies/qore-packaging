
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
