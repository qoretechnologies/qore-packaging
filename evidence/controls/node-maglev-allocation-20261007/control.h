// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
  enum Type : uint8_t {
    kDefault,
    kHeapNumber,
    kFixedDoubleArray,
    kConsString,

    kLast = kConsString
  };
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
