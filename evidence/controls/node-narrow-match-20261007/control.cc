// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Unchanged matcher and narrowing bodies with typed graph-index adapters.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <optional>
#include <type_traits>
void require(bool b) { if(!b) { std::abort(); } }
#define DCHECK(a) require(a)
#define DCHECK_EQ(a,b) require((a)==(b))
[[noreturn]] void unreachable() { std::abort(); }
#define UNREACHABLE() unreachable()
struct OpIndex { int id=-1; bool valid() const { return id>=0; } };
struct Any {};
template<class T> using V=OpIndex;
struct ConstantOp {
  enum class Kind : uint8_t {
    kWord32,
    kWord64,
    kFloat32,
    kFloat64,
    kSmi,
    kNumber,  // TODO(tebbi): See if we can avoid number constants.
    kTaggedIndex,
    kExternal,
    kHeapObject,
    kCompressedHeapObject,
    kTrustedHeapObject,
    kRelocatableWasmCall,
    kRelocatableWasmStubCall,
    kRelocatableWasmIndirectCallTarget,
    kRelocatableWasmCanonicalSignatureId
  };
 Kind kind;
 struct Storage {uint64_t integral;} storage;
 bool IsIntegral() const {return kind==Kind::kWord32||kind==Kind::kWord64||kind==Kind::kRelocatableWasmCanonicalSignatureId;}
  int64_t signed_integral() const {
    DCHECK(IsIntegral());
    switch (kind) {
      case Kind::kWord32:
      case Kind::kRelocatableWasmCanonicalSignatureId:
        return static_cast<int32_t>(storage.integral);
      case Kind::kWord64:
        return static_cast<int64_t>(storage.integral);
      default:
        UNREACHABLE();
    }
  }
};
struct Operation {
 std::optional<ConstantOp> constant;
 std::array<OpIndex,2> inputs;
 template<class T> const T* TryCast() const { static_assert(std::is_same_v<T,ConstantOp>); return constant?&*constant:nullptr; }
};
struct InstructionSelectorT {
 std::array<Operation,4> graph;
 const Operation& Get(OpIndex n) const { require(n.valid());return graph.at(n.id); }
 template<class T> const T* TryCast(OpIndex n) const { return Get(n).template TryCast<T>(); }
 unsigned value_input_count(OpIndex n) const { require(n.id==3);return 2; }
 OpIndex input_at(OpIndex n,unsigned i) const {return Get(n).inputs.at(i);}
  bool MatchSignedIntegralConstant(V<Any> matched, int64_t* constant) const {
    if (const ConstantOp* c = TryCast<ConstantOp>(matched)) {
      if (c->kind == ConstantOp::Kind::kWord32 ||
          c->kind == ConstantOp::Kind::kWord64) {
        *constant = c->signed_integral();
        return true;
      }
    }
    return false;
  }
};
struct MachineType {
 enum class Kind {None,Int8,Uint8,Int16,Uint16,Int32,Uint32};
 Kind kind;
 static MachineType None() {return {Kind::None};}
 static MachineType Int8() {return {Kind::Int8};}
 static MachineType Uint8() {return {Kind::Uint8};}
 static MachineType Int16() {return {Kind::Int16};}
 static MachineType Uint16() {return {Kind::Uint16};}
 static MachineType Int32() {return {Kind::Int32};}
 static MachineType Uint32() {return {Kind::Uint32};}
};
bool IsIntConstant(InstructionSelectorT* selector, OpIndex node) {
  if (auto constant = selector->Get(node).TryCast<ConstantOp>()) {
    return constant->kind == ConstantOp::Kind::kWord32 ||
           constant->kind == ConstantOp::Kind::kWord64;
  }
  return false;
}
__attribute__((noinline))
MachineType MachineTypeForNarrowWordAnd(InstructionSelectorT* selector,
                                        OpIndex and_node,
                                        OpIndex constant_node) {
  DCHECK_EQ(selector->value_input_count(and_node), 2);
  auto and_left = selector->input_at(and_node, 0);
  auto and_right = selector->input_at(and_node, 1);
  auto and_constant_node = IsIntConstant(selector, and_right)  ? and_right
                           : IsIntConstant(selector, and_left) ? and_left
                                                               : OpIndex{};

  if (and_constant_node.valid()) {
    int64_t and_constant, cmp_constant;
    selector->MatchSignedIntegralConstant(and_constant_node, &and_constant);
    selector->MatchSignedIntegralConstant(constant_node, &cmp_constant);
    if (and_constant >= 0 && cmp_constant >= 0) {
      int64_t constant =
          and_constant > cmp_constant ? and_constant : cmp_constant;
      if (constant <= std::numeric_limits<int8_t>::max()) {
        return MachineType::Int8();
      } else if (constant <= std::numeric_limits<uint8_t>::max()) {
        return MachineType::Uint8();
      } else if (constant <= std::numeric_limits<int16_t>::max()) {
        return MachineType::Int16();
      } else if (constant <= std::numeric_limits<uint16_t>::max()) {
        return MachineType::Uint16();
      } else if (constant <= std::numeric_limits<int32_t>::max()) {
        return MachineType::Int32();
      } else if (constant <= std::numeric_limits<uint32_t>::max()) {
        return MachineType::Uint32();
      }
    }
  }

  return MachineType::None();
}
MachineType::Kind expected(int64_t a,int64_t b) {
 using K=MachineType::Kind;
 if(a<0||b<0) {return K::None;}
 uint64_t maximum=static_cast<uint64_t>(a>b?a:b);
 const std::array results{K::Int8,K::Uint8,K::Int16,K::Uint16,K::Int32,K::Uint32};
 const std::array bits{7u,8u,15u,16u,31u,32u};
 for(unsigned i=0;i<bits.size();++i) {if(maximum<(uint64_t{1}<<bits[i])) {return results[i];}}
 return K::None;
}
int64_t canonical(ConstantOp::Kind kind,int64_t value) {
 return kind==ConstantOp::Kind::kWord32?static_cast<int32_t>(value):value;
}
ConstantOp make(ConstantOp::Kind kind,int64_t value) {
 uint64_t bits=static_cast<uint64_t>(value);
 if(kind==ConstantOp::Kind::kWord32) {bits=static_cast<uint32_t>(bits);}
 return {kind,{bits}};
}
int main() {
 using C=ConstantOp::Kind;using M=MachineType::Kind;
 constexpr std::array<int64_t,22> values{INT64_MIN,-4294967297LL,-2147483649LL,-2147483648LL,-1,0,1,126,127,128,254,255,256,32767,32768,65535,65536,2147483647LL,2147483648LL,4294967295LL,4294967296LL,INT64_MAX};
 unsigned checks=0;
 for(unsigned repeat=0;repeat<100;++repeat) {
  for(C ak:{C::kWord32,C::kWord64}) {
   for(C bk:{C::kWord32,C::kWord64}) {
    for(int side:{0,1}) {
     for(int64_t a:values) {for(int64_t b:values) {
      InstructionSelectorT selector{};selector.graph[side].constant=make(ak,a);selector.graph[2].constant=make(bk,b);
      selector.graph[3].inputs={OpIndex{0},OpIndex{1}};
      require(IsIntConstant(&selector,{side})&&IsIntConstant(&selector,{2}));
      auto result=MachineTypeForNarrowWordAnd(&selector,{3},{2});
      require(result.kind==expected(canonical(ak,a),canonical(bk,b)));++checks;
     }}
    }
   }
  }
  for(unsigned raw=0;raw<=static_cast<unsigned>(C::kRelocatableWasmCanonicalSignatureId);++raw) {
   C kind=static_cast<C>(raw);InstructionSelectorT selector{};selector.graph[0].constant=make(kind,123);
   int64_t value=-999;bool matched=selector.MatchSignedIntegralConstant({0},&value);
   bool allowed=kind==C::kWord32||kind==C::kWord64;
   require(IsIntConstant(&selector,{0})==allowed&&matched==allowed);
   require(value==(allowed?123:-999));++checks;
  }
  InstructionSelectorT none{};none.graph[2].constant=make(C::kWord64,0);none.graph[3].inputs={OpIndex{0},OpIndex{1}};
  require(!IsIntConstant(&none,{0}));int64_t sentinel=-99;require(!none.MatchSignedIntegralConstant({0},&sentinel)&&sentinel==-99);
  require(MachineTypeForNarrowWordAnd(&none,{3},{2}).kind==M::None);++checks;
  // With two constants on the AND, the unchanged implementation prefers right.
  none.graph[0].constant=make(C::kWord64,65536);none.graph[1].constant=make(C::kWord64,127);
  require(MachineTypeForNarrowWordAnd(&none,{3},{2}).kind==M::Int8);++checks;
 }
 std::printf("PASS: %u matcher, narrowing-boundary and rejection checks\n",checks);
}
