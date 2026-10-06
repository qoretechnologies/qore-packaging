// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Unchanged upstream enum declarations and dispatch bodies; typed output adapters.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <utility>
void require(bool b) { if (!b) { std::abort(); } }
enum class StubCallMode {
  kCallCodeObject,
#if V8_ENABLE_WEBASSEMBLY
  kCallWasmRuntimeStub,
#endif  // V8_ENABLE_WEBASSEMBLY
  kCallBuiltinPointer,
};
enum class TypeofMode { kInside, kNotInside };
struct CallDescriptor {
  enum Kind {
    kCallCodeObject,         // target is a Code object
    kCallJSFunction,         // target is a JSFunction object
    kCallAddress,            // target is a machine pointer
#if V8_ENABLE_WEBASSEMBLY    // ↓ WebAssembly only
    kCallWasmCapiFunction,   // target is a Wasm C API function
    kCallWasmFunction,       // target is a wasm function
    kCallWasmFunctionIndirect,  // target is a wasm function that will be called
                                // indirectly
    kCallWasmImportWrapper,     // target is a wasm import wrapper
#endif                       // ↑ WebAssembly only
    kCallBuiltinPointer,     // target is a builtin pointer
  };
};
enum WasmCallKind {
  kWasmFunction,
  kWasmIndirectFunction,
  kWasmImportWrapper,
  kWasmCapiFunction
};
struct ComparisonOp {
  enum class Kind : uint8_t {
    kEqual,
    kSignedLessThan,
    kSignedLessThanOrEqual,
    kUnsignedLessThan,
    kUnsignedLessThanOrEqual
  };
Kind kind;
};
namespace maglev { struct Call {
  enum class TargetType { kJSFunction, kAny };
};
enum class TaggedToFloat64ConversionType : uint8_t {
  kOnlyNumber,
  kNumberOrBoolean,
  kNumberOrOddball,
};
}
struct ConvertJSPrimitiveToUntaggedOrDeoptOp {
  enum class JSPrimitiveKind : uint8_t {
    kAdditiveSafeInteger,
    kNumber,
    kNumberOrBoolean,
    kNumberOrOddball,
    kNumberOrString,
    kSmi,
  };
};

struct MachineType { unsigned value; static MachineType AnyTagged() { return {11}; } static MachineType Pointer() { return {22}; } };
using Signature=uint64_t;
constexpr uint64_t kInvalidWasmSignatureHash=std::numeric_limits<uint64_t>::max();
namespace wasm { struct SignatureHasher { static inline unsigned calls=0; static uint64_t Hash(const Signature* sig) { ++calls; return *sig; } }; }
enum class Builtin { kCallFunctionForwardVarargs, kCallForwardVarargs, kLoadGlobalICInsideTypeof, kLoadGlobalIC };
struct ForwardNode { maglev::Call::TargetType mode; auto target_type() const { return mode; } };
struct GlobalNode { TypeofMode mode; auto typeof_mode() const { return mode; } };
struct ConversionNode { maglev::TaggedToFloat64ConversionType mode; auto conversion_type() const { return mode; } };
struct ComparisonOutput { bool called=false; bool is_signed=false; bool is_less_than=false; };
__attribute__((noinline)) void Compare(const ComparisonOp* comparison, ComparisonOutput& output) {
    bool is_signed, is_less_than;
    switch (comparison->kind) {
      case ComparisonOp::Kind::kEqual:
        // TODO(nicohartmann@): Add support for equality.
        return;
      case ComparisonOp::Kind::kSignedLessThan:
        is_signed = true;
        is_less_than = true;
        break;
      case ComparisonOp::Kind::kSignedLessThanOrEqual:
        is_signed = true;
        is_less_than = false;
        break;
      case ComparisonOp::Kind::kUnsignedLessThan:
        is_signed = false;
        is_less_than = true;
        break;
      case ComparisonOp::Kind::kUnsignedLessThanOrEqual:
        is_signed = false;
        is_less_than = false;
        break;
    }
output = {true, is_signed, is_less_than};
}
__attribute__((noinline)) std::pair<CallDescriptor::Kind, MachineType> Stub(StubCallMode stub_mode) {
  CallDescriptor::Kind kind;
  MachineType target_type;
  switch (stub_mode) {
    case StubCallMode::kCallCodeObject:
      kind = CallDescriptor::kCallCodeObject;
      target_type = MachineType::AnyTagged();
      break;
#if V8_ENABLE_WEBASSEMBLY
    case StubCallMode::kCallWasmRuntimeStub:
      kind = CallDescriptor::kCallWasmFunction;
      target_type = MachineType::Pointer();
      break;
#endif  // V8_ENABLE_WEBASSEMBLY
    case StubCallMode::kCallBuiltinPointer:
      kind = CallDescriptor::kCallBuiltinPointer;
      target_type = MachineType::AnyTagged();
      break;
  }
return {kind,target_type};
}
#if V8_ENABLE_WEBASSEMBLY
__attribute__((noinline)) std::pair<CallDescriptor::Kind,uint64_t> Wasm(WasmCallKind call_kind, const Signature* fsig) {
  CallDescriptor::Kind descriptor_kind;
  uint64_t signature_hash = kInvalidWasmSignatureHash;

  switch (call_kind) {
    case kWasmFunction:
      descriptor_kind = CallDescriptor::kCallWasmFunction;
      break;
    case kWasmIndirectFunction:
      descriptor_kind = CallDescriptor::kCallWasmFunctionIndirect;
      signature_hash = wasm::SignatureHasher::Hash(fsig);
      break;
    case kWasmImportWrapper:
      descriptor_kind = CallDescriptor::kCallWasmImportWrapper;
      break;
    case kWasmCapiFunction:
      descriptor_kind = CallDescriptor::kCallWasmCapiFunction;
      break;
  }
return {descriptor_kind,signature_hash};
}
#endif
__attribute__((noinline)) Builtin Forward(ForwardNode* node) {
    Builtin builtin;
    switch (node->target_type()) {
      case maglev::Call::TargetType::kJSFunction:
        builtin = Builtin::kCallFunctionForwardVarargs;
        break;
      case maglev::Call::TargetType::kAny:
        builtin = Builtin::kCallForwardVarargs;
        break;
    }
return builtin;
}
__attribute__((noinline)) Builtin Global(GlobalNode* node) {
    Builtin builtin;
    switch (node->typeof_mode()) {
      case TypeofMode::kInside:
        builtin = Builtin::kLoadGlobalICInsideTypeof;
        break;
      case TypeofMode::kNotInside:
        builtin = Builtin::kLoadGlobalIC;
        break;
    }
return builtin;
}
__attribute__((noinline)) auto Convert(ConversionNode* node) {
    ConvertJSPrimitiveToUntaggedOrDeoptOp::JSPrimitiveKind kind;
    switch (node->conversion_type()) {
      case maglev::TaggedToFloat64ConversionType::kOnlyNumber:
        kind = ConvertJSPrimitiveToUntaggedOrDeoptOp::JSPrimitiveKind::kNumber;
        break;
      case maglev::TaggedToFloat64ConversionType::kNumberOrBoolean:
        kind = ConvertJSPrimitiveToUntaggedOrDeoptOp::JSPrimitiveKind::
            kNumberOrBoolean;
        break;
      case maglev::TaggedToFloat64ConversionType::kNumberOrOddball:
        kind = ConvertJSPrimitiveToUntaggedOrDeoptOp::JSPrimitiveKind::
            kNumberOrOddball;
        break;
    }
return kind;
}

int main() {
 using C=ComparisonOp::Kind; using P=ConvertJSPrimitiveToUntaggedOrDeoptOp::JSPrimitiveKind; using M=maglev::TaggedToFloat64ConversionType;
 const std::array<C,5> comparisons{C::kEqual,C::kSignedLessThan,C::kSignedLessThanOrEqual,C::kUnsignedLessThan,C::kUnsignedLessThanOrEqual};
 const std::array<M,3> conversions{M::kOnlyNumber,M::kNumberOrBoolean,M::kNumberOrOddball};
 const std::array<P,3> primitives{P::kNumber,P::kNumberOrBoolean,P::kNumberOrOddball};
 unsigned checks=0;
 for(unsigned repeat=0;repeat<10000;++repeat) {
  for(unsigned i=0;i<comparisons.size();++i) {
   ComparisonOp op{comparisons[i]};ComparisonOutput output{false,true,false};Compare(&op,output);
   if(i==0) { require(!output.called && output.is_signed && !output.is_less_than); }
   else { require(output.called && output.is_signed==(i<3) && output.is_less_than==(i==1||i==3)); }
   ++checks;
  }
  for(auto mode:{StubCallMode::kCallCodeObject,StubCallMode::kCallBuiltinPointer}) {
   auto [kind,type]=Stub(mode);require(type.value==11 && kind==(mode==StubCallMode::kCallCodeObject?CallDescriptor::kCallCodeObject:CallDescriptor::kCallBuiltinPointer));++checks;
  }
#if V8_ENABLE_WEBASSEMBLY
  {auto [kind,type]=Stub(StubCallMode::kCallWasmRuntimeStub);require(kind==CallDescriptor::kCallWasmFunction && type.value==22);++checks;}
  const std::array<WasmCallKind,4> kinds{kWasmFunction,kWasmIndirectFunction,kWasmImportWrapper,kWasmCapiFunction};
  const std::array<CallDescriptor::Kind,4> descriptors{CallDescriptor::kCallWasmFunction,CallDescriptor::kCallWasmFunctionIndirect,CallDescriptor::kCallWasmImportWrapper,CallDescriptor::kCallWasmCapiFunction};
  for(unsigned i=0;i<kinds.size();++i) {
   for(uint64_t sig:{uint64_t(0),uint64_t(1),uint64_t(1)<<63,std::numeric_limits<uint64_t>::max()-1}) {
    unsigned before=wasm::SignatureHasher::calls;auto [kind,hash]=Wasm(kinds[i],&sig);
    require(kind==descriptors[i] && hash==(i==1?sig:kInvalidWasmSignatureHash) && wasm::SignatureHasher::calls==before+(i==1));++checks;
   }
  }
#endif
  for(auto mode:{maglev::Call::TargetType::kJSFunction,maglev::Call::TargetType::kAny}) {
   ForwardNode node{mode};require(Forward(&node)==(mode==maglev::Call::TargetType::kJSFunction?Builtin::kCallFunctionForwardVarargs:Builtin::kCallForwardVarargs));++checks;
  }
  for(auto mode:{TypeofMode::kInside,TypeofMode::kNotInside}) {
   GlobalNode node{mode};require(Global(&node)==(mode==TypeofMode::kInside?Builtin::kLoadGlobalICInsideTypeof:Builtin::kLoadGlobalIC));++checks;
  }
  for(unsigned i=0;i<conversions.size();++i) { ConversionNode node{conversions[i]};require(Convert(&node)==primitives[i]);++checks; }
 }
 std::printf("PASS: %u call, comparison and conversion dispatch checks (WASM=%d)\n",checks,V8_ENABLE_WEBASSEMBLY);
}
