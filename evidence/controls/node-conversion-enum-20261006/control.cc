// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Original enum declarations, pointer predicate, store method and conversion switches.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
void require(bool b) { if (!b) { std::abort(); } }
enum class MachineRepresentation : uint8_t {
  kNone,
  kBit,
  // Integral representations must be consecutive, in order of increasing order.
  kWord8,
  kWord16,
  kWord32,
  kWord64,
  // (uncompressed) MapWord
  // kMapWord is the representation of a map word, i.e. a map in the header
  // of a HeapObject.
  // If V8_MAP_PACKING is disabled, a map word is just the map itself. Hence
  //     kMapWord is equivalent to kTaggedPointer -- in fact it will be
  //     translated to kTaggedPointer during memory lowering.
  // If V8_MAP_PACKING is enabled, a map word is a Smi-like encoding of a map
  //     and some meta data. Memory lowering of kMapWord loads/stores
  //     produces low-level kTagged loads/stores plus the necessary
  //     decode/encode operations.
  // In either case, the kMapWord representation is not used after memory
  // lowering.
  kMapWord,
  kTaggedSigned,       // (uncompressed) Smi
  kTaggedPointer,      // (uncompressed) HeapObject
  kTagged,             // (uncompressed) Object (Smi or HeapObject)
  kCompressedPointer,  // (compressed) HeapObject
  kCompressed,         // (compressed) Object (Smi or HeapObject)
  kProtectedPointer,   // (uncompressed) TrustedObject
  kIndirectPointer,    // (indirect) HeapObject
  // A 64-bit pointer encoded in a way (e.g. as offset) that guarantees it will
  // point into the sandbox.
  kSandboxedPointer,
  // kFloat16RawBits is not a real FP representation! It's representation of a
  // float16 bitcast to a word16, and is used for conversions to and from
  // Float16Array elements. It is not used after machine lowering.
  kFloat16RawBits,
  // FP and SIMD representations must be last, and in order of increasing size.
  kFloat16,
  kFloat32,
  kFloat64,
  kSimd128,
  kSimd256,
  kFirstFPRepresentation = kFloat16,
  kLastRepresentation = kSimd256
};
constexpr inline bool CanBeTaggedPointer(MachineRepresentation rep) {
  return rep == MachineRepresentation::kTagged ||
         rep == MachineRepresentation::kTaggedPointer ||
         rep == MachineRepresentation::kMapWord;
}
enum WriteBarrierKind : uint8_t {
  kNoWriteBarrier,
  kAssertNoWriteBarrier,
  kMapWriteBarrier,
  kPointerWriteBarrier,
  kIndirectPointerWriteBarrier,
  kEphemeronKeyWriteBarrier,
  kFullWriteBarrier
};
enum class StoreToObjectWriteBarrier { kNone, kMap, kFull };
enum class CheckTaggedInputMode : uint8_t {
  kAdditiveSafeInteger,
  kNumber,
  kNumberOrBoolean,
  kNumberOrOddball,
};
namespace maglev {
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
struct TruncateJSPrimitiveToUntaggedOrDeoptOp { using InputRequirement=ConvertJSPrimitiveToUntaggedOrDeoptOp::JSPrimitiveKind; };

using IR=TruncateJSPrimitiveToUntaggedOrDeoptOp::InputRequirement;
struct Params { CheckTaggedInputMode value; CheckTaggedInputMode mode() const { return value; } };
struct GraphNode { Params params; const Params& op() const { return params; } };
const Params& CheckTaggedInputParametersOf(const Params& p) { return p; }
struct MaglevNode { maglev::TaggedToFloat64ConversionType mode; auto conversion_type() const { return mode; } };
struct Node { int id; };
struct Object {};
struct IntPtrT {};
template<class T> using TNode=Node*;
struct RawAssembler {
 MachineRepresentation rep; Node *object=nullptr,*offset=nullptr,*value=nullptr; WriteBarrierKind barrier; unsigned calls=0;
 void StoreToObject(MachineRepresentation r,Node* o,Node* off,Node* v,WriteBarrierKind b) { rep=r;object=o;offset=off;value=v;barrier=b;++calls; }
};
struct CodeAssembler { RawAssembler raw; RawAssembler* raw_assembler() { return &raw; }
 __attribute__((noinline)) void StoreToObject(MachineRepresentation rep,TNode<Object> object,TNode<IntPtrT> offset,Node* value,StoreToObjectWriteBarrier write_barrier);
};
void CodeAssembler::StoreToObject(MachineRepresentation rep,
                                  TNode<Object> object, TNode<IntPtrT> offset,
                                  Node* value,
                                  StoreToObjectWriteBarrier write_barrier) {
  WriteBarrierKind write_barrier_kind;
  switch (write_barrier) {
    case StoreToObjectWriteBarrier::kFull:
      write_barrier_kind = WriteBarrierKind::kFullWriteBarrier;
      break;
    case StoreToObjectWriteBarrier::kMap:
      write_barrier_kind = WriteBarrierKind::kMapWriteBarrier;
      break;
    case StoreToObjectWriteBarrier::kNone:
      if (CanBeTaggedPointer(rep)) {
        write_barrier_kind = WriteBarrierKind::kAssertNoWriteBarrier;
      } else {
        write_barrier_kind = WriteBarrierKind::kNoWriteBarrier;
      }
      break;
  }
  raw_assembler()->StoreToObject(rep, object, offset, value,
                                 write_barrier_kind);
}
__attribute__((noinline)) IR Truncate(GraphNode* node) {
      using IR = TruncateJSPrimitiveToUntaggedOrDeoptOp::InputRequirement;
      IR input_requirement;
      switch (CheckTaggedInputParametersOf(node->op()).mode()) {
        case CheckTaggedInputMode::kAdditiveSafeInteger:
          input_requirement = IR::kAdditiveSafeInteger;
          break;
        case CheckTaggedInputMode::kNumber:
          input_requirement = IR::kNumber;
          break;
        case CheckTaggedInputMode::kNumberOrBoolean:
          input_requirement = IR::kNumberOrBoolean;
          break;
        case CheckTaggedInputMode::kNumberOrOddball:
          input_requirement = IR::kNumberOrOddball;
          break;
      }
return input_requirement;
}
__attribute__((noinline)) IR Convert(const Params& params) {
      ConvertJSPrimitiveToUntaggedOrDeoptOp::JSPrimitiveKind from_kind;
      switch (params.mode()) {
#define CASE(mode)                                                       \
  case CheckTaggedInputMode::k##mode:                                    \
    from_kind =                                                          \
        ConvertJSPrimitiveToUntaggedOrDeoptOp::JSPrimitiveKind::k##mode; \
    break;
        CASE(AdditiveSafeInteger)
        CASE(Number)
        CASE(NumberOrBoolean)
        CASE(NumberOrOddball)
#undef CASE
      }
return from_kind;
}
__attribute__((noinline)) IR MaglevTruncate(MaglevNode* node) {
    TruncateJSPrimitiveToUntaggedOrDeoptOp::InputRequirement input_requirement;
    switch (node->conversion_type()) {
      case maglev::TaggedToFloat64ConversionType::kOnlyNumber:
        input_requirement =
            TruncateJSPrimitiveToUntaggedOrDeoptOp::InputRequirement::kNumber;
        break;
      case maglev::TaggedToFloat64ConversionType::kNumberOrBoolean:
        input_requirement = TruncateJSPrimitiveToUntaggedOrDeoptOp::
            InputRequirement::kNumberOrBoolean;
        break;
      case maglev::TaggedToFloat64ConversionType::kNumberOrOddball:
        input_requirement = TruncateJSPrimitiveToUntaggedOrDeoptOp::
            InputRequirement::kNumberOrOddball;
        break;
    }
return input_requirement;
}

int main() {
 const std::array<CheckTaggedInputMode,4> modes{CheckTaggedInputMode::kAdditiveSafeInteger,CheckTaggedInputMode::kNumber,CheckTaggedInputMode::kNumberOrBoolean,CheckTaggedInputMode::kNumberOrOddball};
 const std::array<IR,4> mapped{IR::kAdditiveSafeInteger,IR::kNumber,IR::kNumberOrBoolean,IR::kNumberOrOddball};
 const std::array<maglev::TaggedToFloat64ConversionType,3> maglev_modes{maglev::TaggedToFloat64ConversionType::kOnlyNumber,maglev::TaggedToFloat64ConversionType::kNumberOrBoolean,maglev::TaggedToFloat64ConversionType::kNumberOrOddball};
 Node nodes[4]{{11},{22},{33},{44}};unsigned checks=0;
 for(unsigned repeat=0;repeat<10000;++repeat) {
  for(size_t i=0;i<modes.size();++i) { GraphNode node{{modes[i]}};require(Truncate(&node)==mapped[i]);require(Convert(node.params)==mapped[i]);checks+=2; }
  for(size_t i=0;i<maglev_modes.size();++i) { MaglevNode node{maglev_modes[i]};require(MaglevTruncate(&node)==mapped[i+1]);++checks; }
  for(unsigned v=0;v<=static_cast<unsigned>(MachineRepresentation::kLastRepresentation);++v) {
   auto rep=static_cast<MachineRepresentation>(v);
   for(auto barrier:{StoreToObjectWriteBarrier::kNone,StoreToObjectWriteBarrier::kMap,StoreToObjectWriteBarrier::kFull}) {
    for(unsigned n=0;n<4;++n) {
     CodeAssembler assembler;Node *object=&nodes[n],*offset=&nodes[(n+1)%4],*value=&nodes[(n+2)%4];assembler.StoreToObject(rep,object,offset,value,barrier);
     WriteBarrierKind expected=kFullWriteBarrier;
     if(barrier==StoreToObjectWriteBarrier::kMap) { expected=kMapWriteBarrier; }
     if(barrier==StoreToObjectWriteBarrier::kNone) {
      expected=(rep==MachineRepresentation::kMapWord||rep==MachineRepresentation::kTagged||rep==MachineRepresentation::kTaggedPointer) ? kAssertNoWriteBarrier : kNoWriteBarrier;
     }
     require(assembler.raw.barrier==expected && assembler.raw.calls==1 && assembler.raw.rep==rep && assembler.raw.object==object && assembler.raw.offset==offset && assembler.raw.value==value);++checks;
    }
   }
  }
 }
 std::printf("PASS: %u conversion and store dispatch checks across all declared input enum values\n",checks);
}
