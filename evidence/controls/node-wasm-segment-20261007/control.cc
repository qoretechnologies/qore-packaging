// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <optional>
#include <vector>
void require(bool b) {if(!b) {std::abort();}}
#ifdef DEBUG
#define DCHECK(x) require(x)
#define DCHECK_IMPLIES(a,b) require(!(a)||(b))
#define DCHECK_LT(a,b) require((a)<(b))
#else
#define DCHECK(x) ((void)0)
#define DCHECK_IMPLIES(a,b) ((void)0)
#define DCHECK_LT(a,b) ((void)0)
#endif
#define UNREACHABLE() std::abort()
struct OpIndex {int id=-1;bool valid() const {return id>=0;}};
struct Any {};struct Object {};
template<class T> using V=OpIndex;
struct Operation {
 virtual ~Operation()=default;
 template<class T> const T* TryCast() const {return dynamic_cast<const T*>(this);}
};
struct ConstantOp:Operation {
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
 Kind kind;struct Storage {uint64_t integral;} storage;
 ConstantOp(Kind k,uint64_t value):kind(k),storage{value} {}
  bool IsIntegral() const {
    return kind == Kind::kWord32 || kind == Kind::kWord64 ||
           kind == Kind::kRelocatableWasmCall ||
           kind == Kind::kRelocatableWasmStubCall ||
           kind == Kind::kRelocatableWasmCanonicalSignatureId ||
           kind == Kind::kRelocatableWasmIndirectCallTarget;
  }
  uint64_t integral() const {
    DCHECK(IsIntegral());
    return storage.integral;
  }

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
struct CallOp:Operation {
 std::vector<OpIndex> inputs;
 explicit CallOp(std::vector<OpIndex> values):inputs(std::move(values)) {}
 OpIndex callee() const {return inputs.at(0);}
 OpIndex input(unsigned index) const {return inputs.at(index);}
};
struct WasmTypeAnnotationOp:Operation {
 OpIndex target;explicit WasmTypeAnnotationOp(OpIndex value):target(value) {}
 OpIndex value() const {return target;}
};
struct DidntThrowOp:Operation {
 OpIndex target;explicit DidntThrowOp(OpIndex value):target(value) {}
 OpIndex throwing_operation() const {return target;}
};
struct Graph {
 std::vector<std::unique_ptr<Operation>> nodes;
 const Operation& Get(OpIndex index) const {require(index.valid());return *nodes.at(index.id);}
 template<class T,class... Args> OpIndex Add(Args&&... args) {
  nodes.push_back(std::make_unique<T>(std::forward<Args>(args)...));return {static_cast<int>(nodes.size()-1)};
 }
};
struct WordRepresentation {
 enum Kind {K32,K64};Kind kind;
 WordRepresentation(Kind k):kind(k) {}
 Kind value() const {return kind;}
 static Kind Word32() {return K32;}
 static Kind Word64() {return K64;}
};
struct OperationMatcher {
 const Graph& graph;
 explicit OperationMatcher(const Graph& value):graph(value) {}
 template<class T> const T* TryCast(OpIndex index) const {return graph.Get(index).template TryCast<T>();}
  bool MatchIntegralWordConstant(V<Any> matched, WordRepresentation rep,
                                 uint64_t* unsigned_constant,
                                 int64_t* signed_constant = nullptr) const {
    const ConstantOp* op = TryCast<ConstantOp>(matched);
    if (!op) return false;
    switch (op->kind) {
      case ConstantOp::Kind::kWord32:
      case ConstantOp::Kind::kWord64:
      case ConstantOp::Kind::kRelocatableWasmCall:
      case ConstantOp::Kind::kRelocatableWasmStubCall:
        if (rep.value() == WordRepresentation::Word32()) {
          if (unsigned_constant) {
            *unsigned_constant = static_cast<uint32_t>(op->integral());
          }
          if (signed_constant) {
            *signed_constant = static_cast<int32_t>(op->signed_integral());
          }
          return true;
        } else if (rep.value() == WordRepresentation::Word64()) {
          if (unsigned_constant) {
            *unsigned_constant = op->integral();
          }
          if (signed_constant) {
            *signed_constant = op->signed_integral();
          }
          return true;
        }
        return false;
      default:
        return false;
    }
    UNREACHABLE();
  }

  bool MatchIntegralWordConstant(V<Any> matched, WordRepresentation rep,
                                 int64_t* signed_constant) const {
    return MatchIntegralWordConstant(matched, rep, nullptr, signed_constant);
  }
  bool MatchIntegralWord32Constant(V<Any> matched, int32_t* constant) const {
    if (int64_t value; MatchIntegralWordConstant(
            matched, WordRepresentation::Word32(), &value)) {
      *constant = static_cast<int32_t>(value);
      return true;
    }
    return false;
  }
  bool MatchWasmStubCallConstant(V<Any> matched, uint64_t* stub_id) const {
    const ConstantOp* op = TryCast<ConstantOp>(matched);
    if (!op) return false;
    if (op->kind != ConstantOp::Kind::kRelocatableWasmStubCall) {
      return false;
    }
    *stub_id = op->integral();
    return true;
  }
};
enum class Builtin:uint64_t {kWasmArrayNewSegment=1,kOther=2,kFirstBytecodeHandler=3};
struct Smi {
 int32_t value;
 static Smi FromInt(int32_t value) {require(value>=-(1<<30) && value<(1<<30));return {value};}
};
#define __ this->
struct Builder {
 Graph graph;bool unreachable=false;
 bool generating_unreachable_operations() const {return unreachable;}
 const Graph& output_graph() const {return graph;}
 OpIndex SmiConstant(Smi value) {return graph.Add<ConstantOp>(ConstantOp::Kind::kSmi,static_cast<uint64_t>(int64_t(value.value)));}
  const CallOp* IsArrayNewSegment(V<Object> array) {
    DCHECK_IMPLIES(!array.valid(), __ generating_unreachable_operations());
    if (__ generating_unreachable_operations()) return nullptr;
    if (const WasmTypeAnnotationOp* annotation =
            __ output_graph().Get(array).TryCast<WasmTypeAnnotationOp>()) {
      array = annotation->value();
    }
    if (const DidntThrowOp* didnt_throw =
            __ output_graph().Get(array).TryCast<DidntThrowOp>()) {
      array = didnt_throw->throwing_operation();
    }
    const CallOp* call = __ output_graph().Get(array).TryCast<CallOp>();
    if (call == nullptr) return nullptr;
    uint64_t stub_id{};
    if (!OperationMatcher(__ output_graph())
             .MatchWasmStubCallConstant(call->callee(), &stub_id)) {
      return nullptr;
    }
    DCHECK_LT(stub_id, static_cast<uint64_t>(Builtin::kFirstBytecodeHandler));
    if (stub_id == static_cast<uint64_t>(Builtin::kWasmArrayNewSegment)) {
      return call;
    }
    return nullptr;
  }
 __attribute__((noinline)) std::optional<int32_t> Shortcut(V<Object> array) {
  if(const CallOp* array_new=IsArrayNewSegment(array)) {
      OpIndex segment_index = array_new->input(1);
      int32_t index_val;
      OperationMatcher(__ output_graph())
          .MatchIntegralWord32Constant(segment_index, &index_val);
      V<Smi> index_smi = __ SmiConstant(Smi::FromInt(index_val));
   return static_cast<int32_t>(graph.Get(index_smi).TryCast<ConstantOp>()->storage.integral);
  }
  return std::nullopt;
 }
};
int main() {
 using K=ConstantOp::Kind;unsigned checks=0;
 for(unsigned repeat=0;repeat<100;++repeat) {
  for(uint32_t index:{0u,1u,127u,128u,255u,256u,65535u,99999u}) {
   for(unsigned wrappers=0;wrappers<4;++wrappers) {
    for(unsigned target=0;target<4;++target) {for(bool unreachable:{false,true}) {
     Builder builder;builder.unreachable=unreachable;
     auto callee=target==2?builder.graph.Add<Operation>():builder.graph.Add<ConstantOp>(K::kRelocatableWasmStubCall,target==1?2:1);
     // This is the producer's Word32Constant(segment_imm.index) contract.
     auto segment=builder.graph.Add<ConstantOp>(K::kWord32,index);
     OpIndex node=target==3?segment:builder.graph.Add<CallOp>(std::vector<OpIndex>{callee,segment});
     if(wrappers&2) {node=builder.graph.Add<DidntThrowOp>(node);}
     if(wrappers&1) {node=builder.graph.Add<WasmTypeAnnotationOp>(node);}
     auto result=builder.Shortcut(node);
     if(target==0 && !unreachable) {require(result && *result==static_cast<int32_t>(index));}
     else {require(!result);}
     ++checks;
    }}
   }
  }
  Builder unreachable;unreachable.unreachable=true;require(!unreachable.Shortcut(OpIndex{}));++checks;
  // Rejected nonintegral inputs must not alter the matcher's output.
  for(K kind:{K::kFloat32,K::kFloat64,K::kSmi,K::kNumber,K::kExternal,K::kHeapObject}) {
   Builder b;auto node=b.graph.Add<ConstantOp>(kind,42);int32_t value=-177;
   require(!OperationMatcher(b.graph).MatchIntegralWord32Constant(node,&value) && value==-177);++checks;
  }
 }
 std::printf("PASS: %u Wasm segment producer, wrapper and matcher checks\n",checks);
}
