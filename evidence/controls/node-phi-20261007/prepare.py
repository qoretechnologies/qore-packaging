# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib
import json
import shutil
root = Path('work/node-obs-diagnostic-20261006/node-v24.18.1')
out = Path('work/node-phi-controls-20261007')
out.mkdir()
extracts = []
def take(path, begin, end):
    source = (root / path).read_text()
    start = source.index(begin)
    body = source[start:source.index(end, start)].rstrip()
    extracts.append(dict(file=path, line=source[:start].count('\n') + 1,
                         body=body, sha256=hashlib.sha256(body.encode()).hexdigest()))
    return body
hoist = take('deps/v8/src/maglev/maglev-phi-representation-selector.h', '  enum class HoistType', '\n  using HoistTypeList')
representation = take('deps/v8/src/maglev/maglev-ir.h', 'enum class ValueRepresentation', '\n\ninline constexpr')
body = take('deps/v8/src/maglev/maglev-phi-representation-selector.cc', '      BasicBlock* block;\n      DeoptFrame* deopt_frame;', '\n    } else {\n      TRACE_UNTAGGING(TRACE_INPUT_LABEL << ": Invalid input')
source = r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Verbatim phi-hoisting branch, with typed graph/arena adapters.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <initializer_list>
#include <memory>
#include <new>
#include <vector>
void require(bool condition) { if (!condition) { std::abort(); } }
struct Rejected {};
[[noreturn]] void unreachable() { throw Rejected{}; }
#define UNREACHABLE() unreachable()
#define CHECK(a) require(a)
#define CHECK_EQ(a,b) require((a)==(b))
#ifdef DEBUG
#define DCHECK(a) require(a)
#else
#define DCHECK(a) ((void)0)
#endif
'''+hoist+'\n'+representation+r'''
enum class Kind {Input,UnsafeSmiUntag,CheckedNumberOrOddballToFloat64,CheckedTruncateFloat64ToInt32,
 UncheckedNumberOrOddballToFloat64,CheckedHoleyFloat64ToFloat64};
struct InitialValue {};
struct ValueNode {
 Kind kind=Kind::Input;
 ValueNode* input=nullptr;
 bool initial=false;
 template<class T> bool Is() const { static_assert(std::is_same_v<T,InitialValue>); return initial; }
};
struct UnsafeSmiUntag { static constexpr Kind kind=Kind::UnsafeSmiUntag; };
struct CheckedNumberOrOddballToFloat64 { static constexpr Kind kind=Kind::CheckedNumberOrOddballToFloat64; };
struct CheckedTruncateFloat64ToInt32 { static constexpr Kind kind=Kind::CheckedTruncateFloat64ToInt32; };
struct UncheckedNumberOrOddballToFloat64 { static constexpr Kind kind=Kind::UncheckedNumberOrOddballToFloat64; };
struct CheckedHoleyFloat64ToFloat64 { static constexpr Kind kind=Kind::CheckedHoleyFloat64ToFloat64; };
enum class TaggedToFloat64ConversionType {kOnlyNumber};
enum class NodeType {kSmi,kNumber};
NodeType StaticTypeForNode(int,int,ValueNode*) { return NodeType::kSmi; }
bool NodeTypeIs(NodeType actual,NodeType expected) { return actual==expected || (actual==NodeType::kSmi&&expected==NodeType::kNumber); }
struct DeoptFrame { unsigned id; };
struct CheckpointedJump {
 DeoptFrame frame;
 template<class T> T* Cast() { static_assert(std::is_same_v<T,CheckpointedJump>); return this; }
 CheckpointedJump* eager_deopt_info() { return this; }
 DeoptFrame& top_frame() { return frame; }
};
struct BasicBlock {
 CheckpointedJump control;
 CheckpointedJump* control_node() { return &control; }
};
struct Zone {
 std::vector<std::unique_ptr<ValueNode>> nodes;
 int budget=-1;
 template<class T> ValueNode* create(ValueNode* input) {
  if(budget==0) { throw std::bad_alloc(); }
  if(budget>0) { --budget; }
  auto node=std::make_unique<ValueNode>(ValueNode{T::kind,input,false});
  auto* ptr=node.get(); nodes.push_back(std::move(node)); return ptr;
 }
};
struct NodeBase {
 template<class T,class... Args> static ValueNode* New(Zone* zone,std::initializer_list<ValueNode*> inputs,Args...) {
  require(inputs.size()==1); return zone->create<T>(*inputs.begin());
 }
};
struct Phi {
 std::array<BasicBlock*,2> predecessors;
 ValueNode* changed=nullptr;
 int changed_index=-1;
 bool loop;
 Phi* merge_state() { return this; }
 BasicBlock* predecessor_at(int i) { return predecessors.at(i); }
 bool is_loop_phi() const { return loop; }
 bool is_backedge_offset(int i) const { return i==2; }
 bool uses_require_31_bit_value() const { return false; }
 void change_input(int i,ValueNode* value) { require(i>=0&&i<2&&value); changed=value;changed_index=i; }
};
struct Builder {
 Zone arena;
 std::array<BasicBlock*,1> blocks;
 Zone* zone() { return &arena; }
 std::array<BasicBlock*,1>* graph() { return &blocks; }
 int broker() const { return 0; }
 int local_isolate() const { return 0; }
};
struct Selector {
 struct Emission { ValueNode* node;BasicBlock* block;DeoptFrame* frame; };
 Builder* builder_;
 std::vector<Emission> emissions;
 ValueNode* AddNodeAtBlockEnd(ValueNode* node,BasicBlock* block,DeoptFrame* frame=nullptr) {
  require(node&&block);emissions.push_back({node,block,frame});return node;
 }
 __attribute__((noinline)) void Convert(Phi* phi,ValueNode* input,ValueRepresentation repr,
     const std::array<HoistType,2>& hoist_untagging,int input_index) {
'''+body+r'''
 }
};
int main() {
 unsigned checks=0;
 using R=ValueRepresentation;using H=HoistType;
 const std::array reps{R::kInt32,R::kFloat64,R::kHoleyFloat64};
 for(unsigned repeat=0;repeat<1000;++repeat) {
  for(H hoist:{H::kLoopEntryUnchecked,H::kLoopEntry,H::kPrologue}) {
   for(R repr:reps) {
    for(bool loop:{false,true}) {
     for(int index:{0,1}) {
      for(int budget:{-1,0,1,2}) {
       BasicBlock entry{{{1}}},first{{{2}}},second{{{3}}};
       ValueNode input;input.initial=!loop;
       Phi phi{{&first,&second},nullptr,-1,loop};Builder builder;builder.blocks={&entry};builder.arena.budget=budget;
       Selector selector{&builder,{}};
       const bool checked=hoist!=H::kLoopEntryUnchecked;
       const unsigned length=checked&&repr!=R::kHoleyFloat64?2:1;
       bool failed=false;
       try { selector.Convert(&phi,&input,repr,{hoist,hoist},index); }
       catch(const std::bad_alloc&) { failed=true; }
       require(failed==(budget>=0&&static_cast<unsigned>(budget)<length));
       if(failed) { require(!phi.changed&&phi.changed_index==-1); }
       else {
        require(phi.changed&&phi.changed_index==index&&selector.emissions.size()==length);
        BasicBlock* block=hoist==H::kPrologue?&entry:(index?&second:&first);
        DeoptFrame* frame=checked?&block->control.frame:nullptr;
        auto* value=&input;
        for(unsigned i=0;i<length;++i) {
         const auto& emission=selector.emissions[i];
         require(emission.block==block&&emission.frame==frame&&emission.node->input==value);
         Kind expected=i==1?(repr==R::kInt32?Kind::CheckedTruncateFloat64ToInt32:Kind::CheckedHoleyFloat64ToFloat64):
            checked?Kind::CheckedNumberOrOddballToFloat64:
            repr==R::kInt32?Kind::UnsafeSmiUntag:Kind::UncheckedNumberOrOddballToFloat64;
         require(emission.node->kind==expected);value=emission.node;
        }
        require(phi.changed==value);
       }
       ++checks;
      }
     }
    }
   }
  }
  for(H hoist:{H::kNone,H::kLoopEntryUnchecked,H::kLoopEntry,H::kPrologue}) {
   for(R repr:{R::kTagged,R::kInt32,R::kUint32,R::kFloat64,R::kHoleyFloat64,R::kIntPtr}) {
    if(hoist!=H::kNone&&(repr==R::kInt32||repr==R::kFloat64||repr==R::kHoleyFloat64)) { continue; }
    BasicBlock block{{{1}}};ValueNode input;input.initial=true;
    Phi phi{{&block,&block},nullptr,-1,false};Builder builder;builder.blocks={&block};Selector selector{&builder,{}};
    bool rejected=false;
    try { selector.Convert(&phi,&input,repr,{hoist,hoist},0); } catch(const Rejected&) { rejected=true; }
    require(rejected&&!phi.changed&&builder.arena.nodes.empty()&&selector.emissions.empty());++checks;
   }
  }
 }
 std::printf("PASS: %u phi conversion, allocation-failure and rejection checks\n",checks);
}
'''
(out/'control.cc').write_text(source)
(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n')
shutil.copy2(root/'deps/v8/LICENSE',out/'V8-LICENSE')
shutil.copy2('work/node-object-dispatch-controls-20261007/run.py',out/'run.py')
