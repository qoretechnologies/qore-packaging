# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil
root=Path('work/node-obs-diagnostic-20261006/node-v24.18.1');out=Path('work/node-structural-cascade-controls-20261007');out.mkdir()
path='deps/v8/src/compiler/turboshaft/structural-optimization-reducer.h';s=(root/path).read_text();a=s.index('  OpIndex ReduceInputGraphBranch(');b=s.index('\n private:',a);body=s[a:b]
(out/'source-extracts.json').write_text(json.dumps([dict(file=path,line=s[:a].count('\n')+1,body=body,sha256=hashlib.sha256(body.encode()).hexdigest())],indent=2)+'\n')
(out/'control.h').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <type_traits>
#include <vector>
inline void require(bool c) {if(!c) {std::abort();}}
#define TRACE(...) ((void)0)
#define CHECK_EQ(a,b) require((a)==(b))
#ifdef DEBUG
#define DCHECK(x) require(bool(x))
#define DCHECK_NE(a,b) require((a)!=(b))
#else
#define DCHECK(x) ((void)0)
#define DCHECK_NE(a,b) ((void)0)
#endif
#define LABEL_BLOCK(label) for (;false;std::abort()) label:
struct OpIndex {
  int value;
  static OpIndex Invalid() {return {-1};}
  bool valid() const {return value>=0;}
  bool operator==(const OpIndex&) const=default;
};
enum class BranchHint {kNone,kTrue,kFalse};
struct ComparisonOp;struct ConstantOp;struct BranchOp;struct Block;struct Graph;
namespace Opmask {struct kWord32Equal {};struct kWord32Constant {};}
struct Operation {
  enum class Kind {Var,Equal,OtherComparison,Constant,OtherConstant,Branch,End};
  const Kind kind;
  explicit Operation(Kind k):kind(k) {}
  virtual ~Operation()=default;
  template<class T> bool Is() const;
  template<class T> const T& Cast() const {require(Is<T>());return static_cast<const T&>(*this);}
  template<class T> const ComparisonOp* TryCast() const;
};
struct ComparisonOp:Operation {
  OpIndex lhs,rhs;
  ComparisonOp(OpIndex left,OpIndex right,bool eq=true):Operation(eq?Kind::Equal:Kind::OtherComparison),lhs(left),rhs(right) {}
  OpIndex left() const {return lhs;} OpIndex right() const {return rhs;}
};
struct ConstantOp:Operation {
  uint32_t value;
  ConstantOp(uint32_t v,bool word=true):Operation(word?Kind::Constant:Kind::OtherConstant),value(v) {}
  uint32_t word32() const {return value;}
};
struct BranchOp:Operation {
  OpIndex cond;Block* if_true;Block* if_false;BranchHint hint;
  BranchOp(OpIndex c,Block* t,Block* f,BranchHint h):Operation(Kind::Branch),cond(c),if_true(t),if_false(f),hint(h) {}
  OpIndex condition() const {return cond;}
};
template<class T> bool Operation::Is() const {
  if constexpr(std::is_same_v<T,ComparisonOp>) {return kind==Kind::Equal||kind==Kind::OtherComparison;}
  else if constexpr(std::is_same_v<T,ConstantOp>||std::is_same_v<T,Opmask::kWord32Constant>) {return kind==Kind::Constant;}
  else if constexpr(std::is_same_v<T,BranchOp>) {return kind==Kind::Branch;}
  else {std::abort();}
}
template<class T> const ComparisonOp* Operation::TryCast() const {
  static_assert(std::is_same_v<T,Opmask::kWord32Equal>);
  return kind==Kind::Equal?static_cast<const ComparisonOp*>(this):nullptr;
}
struct Block {
  unsigned id;
  bool pure=true;
  OpIndex last=OpIndex::Invalid();
  const Operation& LastOperation(const Graph&) const;
};
struct Graph {
  std::vector<std::unique_ptr<Operation>> operations;
  std::vector<std::unique_ptr<Block>> blocks;
  template<class T,class... A> OpIndex add(A&&... args) {
    operations.push_back(std::make_unique<T>(std::forward<A>(args)...));return {static_cast<int>(operations.size()-1)};
  }
  Block* block() {auto b=std::make_unique<Block>();b->id=blocks.size();auto* p=b.get();blocks.push_back(std::move(b));return p;}
  const Operation& Get(OpIndex index) const {require(index.valid()&&size_t(index.value)<operations.size());return *operations[index.value];}
};
struct SwitchOp {struct Case {uint32_t value;Block* destination;BranchHint hint;Case(uint32_t v,Block* d,BranchHint h):value(v),destination(d),hint(h) {}};};
namespace base {template<class T,unsigned N> using SmallVector=std::vector<T>;}
struct NextReducer {static OpIndex ReduceInputGraphBranch(OpIndex,const BranchOp&) {return {0};}};
template<class Next> struct StructuralOptimizationReducer:Next {
  Graph graph;bool skip=false;
  std::vector<SwitchOp::Case> emitted;
  std::vector<const Block*> inlined;
  Block* default_block=nullptr;BranchHint default_hint=BranchHint::kNone;OpIndex switched=OpIndex::Invalid();
  bool ShouldSkipOptimizationStep() const {return skip;}
  auto& Asm() {return *this;}
  Graph& input_graph() {return graph;}
  Block* MapToNewGraph(Block* b) {return b;}
  static bool ContainsOnlyPureOps(const Block* block,const Graph&) {return block->pure;}
  OpIndex EmitSwitch(OpIndex variable,base::SmallVector<SwitchOp::Case,16>& cases,base::SmallVector<const Block*,16>& false_blocks,Block* last,BranchHint hint) {
    require(last && false_blocks.back()==last);switched=variable;emitted=cases;inlined=false_blocks;default_block=last;default_hint=hint;return {99};
  }
'''+body+r'''
};
''')
(out/'helper.cc').write_text('''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
const Operation& Block::LastOperation(const Graph& graph) const {return graph.Get(last);}
''')
(out/'control.cc').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
''')
shutil.copy2(root/'deps/v8/LICENSE',out/'V8-LICENSE');shutil.copy2('work/node-wasm-grow-controls-20261007/run.py',out/'run.py')
print('Prepared complete unchanged cascade reducer with typed graph adapters.')
