# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib, json, shutil

root = Path('work/node-obs-diagnostic-20261006/node-v24.18.1')
out = Path('work/node-maglev-allocation-controls-20261007')
out.mkdir()
path = 'deps/v8/src/maglev/maglev-graph-builder.cc'
source = (root / path).read_text()
start = source.index('InlinedAllocation* MaglevGraphBuilder::BuildInlinedAllocation(\n')
end = source.index('\nValueNode* MaglevGraphBuilder::BuildInlinedArgumentsElements', start)
body = source[start:end]
enum_path = 'deps/v8/src/maglev/maglev-ir.h'
enum_source = (root / enum_path).read_text()
enum_start = enum_source.index('  enum Type : uint8_t {', enum_source.index('class VirtualObject :'))
enum_end = enum_source.index('\n  };', enum_start) + len('\n  };')
enum = enum_source[enum_start:enum_end]
(out / 'source-extracts.json').write_text(json.dumps([
    dict(file=path, line=source[:start].count('\n')+1, body=body, sha256=hashlib.sha256(body.encode()).hexdigest()),
    dict(file=enum_path, line=enum_source[:enum_start].count('\n')+1, body=enum, sha256=hashlib.sha256(enum.encode()).hexdigest()),
], indent=2)+'\n')
(out / 'control.h').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <set>
#include <stdexcept>
#include <utility>
#include <vector>
inline void require(bool condition) { if (!condition) { std::abort(); } }
constexpr int kTaggedSize=8;
enum class AllocationType { kYoung, kOld };
struct ValueNode {
  enum class Kind { Tagged, Float, Virtual, Allocation };
  const Kind kind;
  explicit ValueNode(Kind k):kind(k) { ++live; }
  virtual ~ValueNode() { --live; }
  ValueNode(const ValueNode&)=delete;
  ValueNode& operator=(const ValueNode&)=delete;
  static inline unsigned live=0;
  template<class T> bool Is() const { return kind==T::node_kind; }
  template<class T> T* Cast() { require(Is<T>()); return static_cast<T*>(this); }
};
struct TaggedValue : ValueNode {
  static constexpr Kind node_kind=Kind::Tagged;
  int value;
  explicit TaggedValue(int v):ValueNode(node_kind),value(v) {}
};
struct Float64Constant : ValueNode {
  static constexpr Kind node_kind=Kind::Float;
  double value_;
  explicit Float64Constant(double v):ValueNode(node_kind),value_(v) {}
  double value() const { return value_; }
};
struct VirtualObject : ValueNode {
  static constexpr Kind node_kind=Kind::Virtual;
'''+enum+r'''
  const Type type_;
  const bool static_map;
  const int map_;
  double number=0;
  std::vector<ValueNode*> inputs;
  VirtualObject(Type type, bool has_map, int map):ValueNode(node_kind),type_(type),static_map(has_map),map_(map) {}
  Type type() const;
  bool has_static_map() const { return static_map; }
  int map() const { return map_; }
  template<class F> void ForEachInput(F f) { for (auto*& n:inputs) { f(n); } }
};
struct InlinedAllocation : ValueNode {
  static constexpr Kind node_kind=Kind::Allocation;
  const VirtualObject::Type type;
  const AllocationType generation;
  const double number;
  unsigned uses=0;
  int map=-1;
  std::vector<std::pair<int,ValueNode*>> stores;
  InlinedAllocation(VirtualObject* v,AllocationType a):ValueNode(node_kind),type(v->type()),generation(a),number(v->number) {}
};
struct StoreMap { enum class Kind { kInlinedAllocation }; };
struct Frame { std::vector<VirtualObject*> objects; void add_object(VirtualObject* v) { objects.push_back(v); } };
struct Effects { std::set<InlinedAllocation*> allocations; };
template<class T,unsigned N> struct SmallZoneVector:std::vector<T> { explicit SmallZoneVector(void*) {} };
struct Flags { unsigned maglev_allocation_folding=0; };
extern Flags v8_flags;
struct MaglevGraphBuilder {
  Frame current_interpreter_frame_;
  Effects effects;
  Effects* loop_effects_=&effects;
  bool loop=false;
  unsigned clears=0;
  unsigned calls=0;
  int fail_at=-1;
  std::vector<std::unique_ptr<ValueNode>> arena;
  void* zone() { return nullptr; }
  template<class T,class... A> T* make(A&&... args) {
    if (static_cast<int>(calls++)==fail_at) { throw std::bad_alloc(); }
    auto node=std::make_unique<T>(std::forward<A>(args)...);
    auto* result=node.get(); arena.push_back(std::move(node)); return result;
  }
  InlinedAllocation* ExtendOrReallocateCurrentAllocationBlock(AllocationType a,VirtualObject* v) { return make<InlinedAllocation>(v,a); }
  InlinedAllocation* BuildInlinedAllocationForHeapNumber(VirtualObject* v,AllocationType a) { return ExtendOrReallocateCurrentAllocationBlock(a,v); }
  InlinedAllocation* BuildInlinedAllocationForDoubleFixedArray(VirtualObject* v,AllocationType a) { return ExtendOrReallocateCurrentAllocationBlock(a,v); }
  InlinedAllocation* BuildInlinedAllocationForConsString(VirtualObject* v,AllocationType a) { return ExtendOrReallocateCurrentAllocationBlock(a,v); }
  VirtualObject* CreateHeapNumber(double number) { auto* v=make<VirtualObject>(VirtualObject::kHeapNumber,true,42);v->number=number;return v; }
  ValueNode* GetTaggedValue(ValueNode* n) { require(n->Is<TaggedValue>()||n->Is<InlinedAllocation>());return n; }
  void AddNonEscapingUses(InlinedAllocation* a,int count) { require(count>=0);a->uses+=count; }
  void BuildStoreMap(InlinedAllocation* a,int map,StoreMap::Kind) { a->map=map; }
  void BuildInitializeStore(InlinedAllocation* a,ValueNode* n,int offset) { a->stores.emplace_back(offset,n); }
  bool is_loop_effect_tracking() const { return loop; }
  void ClearCurrentAllocationBlock() { ++clears; }
  InlinedAllocation* BuildInlinedAllocation(VirtualObject*,AllocationType);
};
''')
(out/'helper.cc').write_text('''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
VirtualObject::Type VirtualObject::type() const { return type_; }
''')
(out/'control.cc').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
Flags v8_flags{};
'''+body+r'''
struct Expected {
  VirtualObject* node;
  std::vector<ValueNode*> inputs;
};
void verify(MaglevGraphBuilder& builder,InlinedAllocation* result,const Expected& e,AllocationType generation) {
  require(result->type==e.node->type() && result->generation==generation);
  if (e.node->type()!=VirtualObject::kDefault) { return; }
  require(result->stores.size()==e.inputs.size());
  require(result->uses==e.inputs.size()+unsigned(e.node->has_static_map()));
  require(result->map==(e.node->has_static_map()?e.node->map():-1));
  require(builder.effects.allocations.contains(result)==builder.loop);
  for (unsigned i=0;i<e.inputs.size();++i) {
    auto* original=e.inputs[i]; auto* stored=result->stores[i].second;
    require(result->stores[i].first==static_cast<int>((i+1)*kTaggedSize));
    if (original->Is<VirtualObject>()) {
      require(stored->Is<InlinedAllocation>() && e.node->inputs[i]==stored);
      auto* nested=original->Cast<VirtualObject>();
      verify(builder,stored->Cast<InlinedAllocation>(),Expected{nested,{}},generation);
    } else if (original->Is<Float64Constant>()) {
      require(e.node->inputs[i]==original && stored->Is<InlinedAllocation>());
      require(stored->Cast<InlinedAllocation>()->number==original->Cast<Float64Constant>()->value());
    } else { require(stored==original && e.node->inputs[i]==original); }
  }
}
int main() {
  unsigned checks=0,failures=0;
  for (unsigned repeat=0;repeat<30;++repeat) {
    for (auto type:{VirtualObject::kDefault,VirtualObject::kHeapNumber,VirtualObject::kFixedDoubleArray,VirtualObject::kConsString}) {
      for (unsigned fields:{0u,1u,8u,12u}) {for (unsigned mode=0;mode<12;++mode) {
        for (auto generation:{AllocationType::kYoung,AllocationType::kOld}) {
          for (int fail=-1;fail<12;++fail) {
            {
              MaglevGraphBuilder b;b.loop=mode&1;v8_flags.maglev_allocation_folding=mode/4;
              auto* v=b.make<VirtualObject>(type,bool(mode&2),171);
              for (unsigned i=0;i<fields;++i) {
                if (i%3==0) {v->inputs.push_back(b.make<VirtualObject>(static_cast<VirtualObject::Type>((i/3)%4),true,172));}
                else if (i%3==1) {v->inputs.push_back(b.make<Float64Constant>(i+0.25));}
                else {v->inputs.push_back(b.make<TaggedValue>(i));}
              }
              Expected expected{v,v->inputs};b.calls=0;b.fail_at=fail;
              try {
                auto* allocation=b.BuildInlinedAllocation(v,generation);
                verify(b,allocation,expected,generation);
                require(b.clears==(v8_flags.maglev_allocation_folding<2?b.current_interpreter_frame_.objects.size():0));
                require(fail<0 || static_cast<unsigned>(fail)>=b.calls);
              } catch (const std::bad_alloc&) {
                require(fail>=0 && b.calls==static_cast<unsigned>(fail+1));++failures;
              }
            }
            require(ValueNode::live==0);++checks;
          }
        }
      }}
    }
  }
  std::printf("PASS: %u typed allocation-dispatch cases, including %u injected failures\n",checks,failures);
}
''')
shutil.copy2(root/'deps/v8/LICENSE',out/'V8-LICENSE')
shutil.copy2('work/node-wasm-grow-controls-20261007/run.py',out/'run.py')
print('Prepared unchanged allocation dispatch and exact four-value enum.')
