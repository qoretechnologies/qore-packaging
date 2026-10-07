// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
int main() {
  unsigned checks=0;
  for(unsigned repeat=0;repeat<100;++repeat) {
    for(unsigned length=1;length<=7;++length) {for(unsigned defect=0;defect<7;++defect) {
      for(unsigned stop=0;stop<length;++stop) {for(unsigned hint_mode=0;hint_mode<3;++hint_mode) {
        for(bool invert:{false,true}) {for(bool skip:{false,true}) {
          StructuralOptimizationReducer<NextReducer> r;r.skip=skip;auto& g=r.graph;
          auto variable=g.add<Operation>(Operation::Kind::Var);
          auto other=g.add<Operation>(Operation::Kind::Var);
          auto end=g.add<Operation>(Operation::Kind::End);
          std::vector<Block*> chain,targets;
          for(unsigned i=0;i<=length;++i) {auto* b=g.block();b->last=end;chain.push_back(b);}
          for(unsigned i=0;i<length;++i) {auto* b=g.block();b->last=end;targets.push_back(b);}
          std::vector<uint32_t> values;
          for(unsigned i=0;i<length;++i) {
            uint32_t value=i==0?0:100-i*7;
            if(defect==5 && i==stop && i>0) {value=0;}
            values.push_back(value);
            auto constant=g.add<ConstantOp>(value,!(defect==2&&i==stop));
            auto lhs=defect==4&&i==stop?other:variable;
            auto condition=g.add<ComparisonOp>(lhs,constant,!(defect==1&&i==stop));
            bool is_inverted=invert&&i==0;
            if(is_inverted) {condition=variable;}
            auto hint=static_cast<BranchHint>((hint_mode+i)%3);
            chain[i]->last=g.add<BranchOp>(condition,is_inverted?chain[i+1]:targets[i],is_inverted?targets[i]:chain[i+1],hint);
            if(defect==3&&i==stop) {chain[i+1]->pure=false;}
          }
          if(defect==6) {chain[stop+1]->last=end;}
          unsigned included=0;
          for(unsigned i=0;i<length;++i) {
            bool inv=invert&&i==0;
            if(i==stop && ((defect==1&&!inv)||(defect==2&&!inv)||defect==3)) {break;}
            auto first_var=defect==4&&stop==0&&!invert?other:variable;
            auto this_var=defect==4&&i==stop&&!inv?other:variable;
            if(this_var!=first_var) {break;}
            ++included;
            if(defect==6&&i==stop) {break;}
          }
          bool duplicate=defect==5&&stop>0&&stop<included;
          bool should_switch=!skip&&included>2&&!duplicate;
          auto result=r.ReduceInputGraphBranch(chain[0]->last,g.Get(chain[0]->last).Cast<BranchOp>());
          require((result.value==99)==should_switch);
          if(should_switch) {
            require(r.default_block==chain[included] && r.emitted.size()==included && r.inlined.size()==included);
            for(unsigned i=0;i<included;++i) {require(r.inlined[i]==chain[i+1]);}
            for(const auto& c:r.emitted) {
              auto it=std::find(values.begin(),values.begin()+included,c.value);require(it!=values.begin()+included);
              require(c.destination==targets[it-values.begin()]);
            }
            for(unsigned i=1;i<included;++i) {require(r.emitted[i-1].value<r.emitted[i].value);}
          } else {require(result.value==0 && r.emitted.empty() && r.default_block==nullptr);}
          ++checks;
        }}
      }}
    }}
  }
  std::printf("PASS: %u branch-cascade, bailout, purity and destination checks\n",checks);
}
