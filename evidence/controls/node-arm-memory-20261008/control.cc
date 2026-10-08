// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// V8 enum declarations and selector bodies are unchanged BSD-licensed extracts.
// Adapters preserve typed representation values and opcode identities. Fatal
// checks throw only in this standalone control so rejection paths can be counted.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <optional>
#include <tuple>
struct Rejected {};
#define CHECK(x) do { if (!(x)) { throw Rejected{}; } } while (false)
#define UNREACHABLE() do { throw Rejected{}; } while (false)
#ifdef DEBUG
#define DCHECK_EQ(a,b) CHECK((a)==(b))
#else
// Keep adapter types checked without evaluating a release-mode assertion.
#define DCHECK_EQ(a,b) ((void)sizeof((a)==(b)))
#endif
#ifdef V8_COMPRESS_POINTERS
constexpr bool COMPRESS_POINTERS_BOOL=true;
#else
constexpr bool COMPRESS_POINTERS_BOOL=false;
#endif
constexpr bool V8_ENABLE_SANDBOX_BOOL=SANDBOX;
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
enum class MachineSemantic : uint8_t {
  kNone,
  kBool,
  kInt32,
  kUint32,
  kInt64,
  kUint64,
  kSignedBigInt64,
  kUnsignedBigInt64,
  kNumber,
  kHoleyFloat64,
  kAny
};
enum ImmediateMode {
  kArithmeticImm,  // 12 bit unsigned immediate shifted left 0 or 12 bits
  kShift32Imm,     // 0 - 31
  kShift64Imm,     // 0 - 63
  kLogical32Imm,
  kLogical64Imm,
  kLoadStoreImm8,  // signed 8 bit or 12 bit unsigned scaled by access size
  kLoadStoreImm16,
  kLoadStoreImm32,
  kLoadStoreImm64,
  kConditionalCompareImm,
  kNoImmediate
};
enum InstructionCode { kArm64Ldr, kArm64LdrD, kArm64LdrDecodeSandboxedPointer, kArm64LdrDecompressProtected, kArm64LdrDecompressTagged, kArm64LdrDecompressTaggedSigned, kArm64LdrH, kArm64LdrQ, kArm64LdrS, kArm64LdrW, kArm64Ldrb, kArm64Ldrh, kArm64Ldrsb, kArm64LdrsbW, kArm64Ldrsh, kArm64LdrshW, kArm64Str, kArm64StrCompressTagged, kArm64StrD, kArm64StrEncodeSandboxedPointer, kArm64StrH, kArm64StrIndirectPointer, kArm64StrPair, kArm64StrQ, kArm64StrS, kArm64StrW, kArm64StrWPair, kArm64Strb, kArm64Strh };
struct MaybeRegisterRepresentation {
  enum class Enum : uint8_t {
    kWord32,
    kWord64,
    kFloat32,
    kFloat64,
    kTagged,
    kCompressed,
    kSimd128,
    kSimd256,
    kNone,  // No register representation.
  };
};
class MemoryRepresentation {
public:
  enum class Enum : uint8_t {
    kInt8,
    kUint8,
    kInt16,
    kUint16,
    kInt32,
    kUint32,
    kInt64,
    kUint64,
    kFloat16,
    kFloat32,
    kFloat64,
    kAnyTagged,
    kTaggedPointer,
    kTaggedSigned,
    kAnyUncompressedTagged,
    kUncompressedTaggedPointer,
    kUncompressedTaggedSigned,
    kProtectedPointer,
    kIndirectPointer,
    kSandboxedPointer,
    kSimd128,
    kSimd256
  };
explicit constexpr MemoryRepresentation(Enum value):value_(value) {}
constexpr operator Enum() const { return value_; }
static constexpr MemoryRepresentation Int8() { return MemoryRepresentation(Enum::kInt8); }
static constexpr MemoryRepresentation Uint8() { return MemoryRepresentation(Enum::kUint8); }
static constexpr MemoryRepresentation Int16() { return MemoryRepresentation(Enum::kInt16); }
static constexpr MemoryRepresentation Uint16() { return MemoryRepresentation(Enum::kUint16); }
static constexpr MemoryRepresentation Int32() { return MemoryRepresentation(Enum::kInt32); }
static constexpr MemoryRepresentation Uint32() { return MemoryRepresentation(Enum::kUint32); }
static constexpr MemoryRepresentation Int64() { return MemoryRepresentation(Enum::kInt64); }
static constexpr MemoryRepresentation Uint64() { return MemoryRepresentation(Enum::kUint64); }
static constexpr MemoryRepresentation Float16() { return MemoryRepresentation(Enum::kFloat16); }
static constexpr MemoryRepresentation Float32() { return MemoryRepresentation(Enum::kFloat32); }
static constexpr MemoryRepresentation Float64() { return MemoryRepresentation(Enum::kFloat64); }
static constexpr MemoryRepresentation AnyTagged() { return MemoryRepresentation(Enum::kAnyTagged); }
static constexpr MemoryRepresentation TaggedPointer() { return MemoryRepresentation(Enum::kTaggedPointer); }
static constexpr MemoryRepresentation TaggedSigned() { return MemoryRepresentation(Enum::kTaggedSigned); }
static constexpr MemoryRepresentation AnyUncompressedTagged() { return MemoryRepresentation(Enum::kAnyUncompressedTagged); }
static constexpr MemoryRepresentation UncompressedTaggedPointer() { return MemoryRepresentation(Enum::kUncompressedTaggedPointer); }
static constexpr MemoryRepresentation UncompressedTaggedSigned() { return MemoryRepresentation(Enum::kUncompressedTaggedSigned); }
static constexpr MemoryRepresentation ProtectedPointer() { return MemoryRepresentation(Enum::kProtectedPointer); }
static constexpr MemoryRepresentation IndirectPointer() { return MemoryRepresentation(Enum::kIndirectPointer); }
static constexpr MemoryRepresentation SandboxedPointer() { return MemoryRepresentation(Enum::kSandboxedPointer); }
static constexpr MemoryRepresentation Simd128() { return MemoryRepresentation(Enum::kSimd128); }
static constexpr MemoryRepresentation Simd256() { return MemoryRepresentation(Enum::kSimd256); }
private:
Enum value_;
};
class RegisterRepresentation {
public:
  enum class Enum : uint8_t {
    kWord32 = static_cast<int>(MaybeRegisterRepresentation::Enum::kWord32),
    kWord64 = static_cast<int>(MaybeRegisterRepresentation::Enum::kWord64),
    kFloat32 = static_cast<int>(MaybeRegisterRepresentation::Enum::kFloat32),
    kFloat64 = static_cast<int>(MaybeRegisterRepresentation::Enum::kFloat64),
    kTagged = static_cast<int>(MaybeRegisterRepresentation::Enum::kTagged),
    kCompressed =
        static_cast<int>(MaybeRegisterRepresentation::Enum::kCompressed),
    kSimd128 = static_cast<int>(MaybeRegisterRepresentation::Enum::kSimd128),
    kSimd256 = static_cast<int>(MaybeRegisterRepresentation::Enum::kSimd256),
  };
explicit constexpr RegisterRepresentation(Enum value):value_(value) {}
constexpr operator Enum() const { return value_; }
static constexpr RegisterRepresentation Word32() { return RegisterRepresentation(Enum::kWord32); }
static constexpr RegisterRepresentation Word64() { return RegisterRepresentation(Enum::kWord64); }
static constexpr RegisterRepresentation Float32() { return RegisterRepresentation(Enum::kFloat32); }
static constexpr RegisterRepresentation Float64() { return RegisterRepresentation(Enum::kFloat64); }
static constexpr RegisterRepresentation Tagged() { return RegisterRepresentation(Enum::kTagged); }
static constexpr RegisterRepresentation Compressed() { return RegisterRepresentation(Enum::kCompressed); }
static constexpr RegisterRepresentation Simd128() { return RegisterRepresentation(Enum::kSimd128); }
static constexpr RegisterRepresentation Simd256() { return RegisterRepresentation(Enum::kSimd256); }
private:
Enum value_;
};
constexpr int ElementSizeLog2Of(MachineRepresentation) { return COMPRESS_POINTERS_BOOL ? 2 : 3; }
struct LoadRepresentation {
    MachineRepresentation rep;
    MachineSemantic sem;
    MachineRepresentation representation() const { return rep; }
    constexpr MachineSemantic semantic() const { return sem; }
  constexpr bool IsUnsigned() const {
    return semantic() == MachineSemantic::kUint32 ||
           semantic() == MachineSemantic::kUint64;
  }
};
std::tuple<InstructionCode, ImmediateMode> GetStoreOpcodeAndImmediate(
    MemoryRepresentation stored_rep, bool paired) {
  switch (stored_rep) {
    case MemoryRepresentation::Int8():
    case MemoryRepresentation::Uint8():
      CHECK(!paired);
      return {kArm64Strb, kLoadStoreImm8};
    case MemoryRepresentation::Int16():
    case MemoryRepresentation::Uint16():
      CHECK(!paired);
      return {kArm64Strh, kLoadStoreImm16};
    case MemoryRepresentation::Int32():
    case MemoryRepresentation::Uint32():
      return {paired ? kArm64StrWPair : kArm64StrW, kLoadStoreImm32};
    case MemoryRepresentation::Int64():
    case MemoryRepresentation::Uint64():
      return {paired ? kArm64StrPair : kArm64Str, kLoadStoreImm64};
    case MemoryRepresentation::Float16():
      CHECK(!paired);
      return {kArm64StrH, kLoadStoreImm16};
    case MemoryRepresentation::Float32():
      CHECK(!paired);
      return {kArm64StrS, kLoadStoreImm32};
    case MemoryRepresentation::Float64():
      CHECK(!paired);
      return {kArm64StrD, kLoadStoreImm64};
    case MemoryRepresentation::AnyTagged():
    case MemoryRepresentation::TaggedPointer():
    case MemoryRepresentation::TaggedSigned():
      if (paired) {
        // There is an inconsistency here on how we treat stores vs. paired
        // stores. In the normal store case we have special opcodes for
        // compressed fields and the backend decides whether to write 32 or 64
        // bits. However, for pairs this does not make sense, since the
        // paired values could have different representations (e.g.,
        // compressed paired with word32). Therefore, we decide on the actual
        // machine representation already in instruction selection.
#ifdef V8_COMPRESS_POINTERS
        static_assert(ElementSizeLog2Of(MachineRepresentation::kTagged) == 2);
        return {kArm64StrWPair, kLoadStoreImm32};
#else
        static_assert(ElementSizeLog2Of(MachineRepresentation::kTagged) == 3);
        return {kArm64StrPair, kLoadStoreImm64};
#endif
      }
      return {kArm64StrCompressTagged,
              COMPRESS_POINTERS_BOOL ? kLoadStoreImm32 : kLoadStoreImm64};
    case MemoryRepresentation::AnyUncompressedTagged():
    case MemoryRepresentation::UncompressedTaggedPointer():
    case MemoryRepresentation::UncompressedTaggedSigned():
      CHECK(!paired);
      return {kArm64Str, kLoadStoreImm64};
    case MemoryRepresentation::ProtectedPointer():
      // We never store directly to protected pointers from generated code.
      UNREACHABLE();
    case MemoryRepresentation::IndirectPointer():
      return {kArm64StrIndirectPointer, kLoadStoreImm32};
    case MemoryRepresentation::SandboxedPointer():
      CHECK(!paired);
      return {kArm64StrEncodeSandboxedPointer, kLoadStoreImm64};
    case MemoryRepresentation::Simd128():
      CHECK(!paired);
      return {kArm64StrQ, kNoImmediate};
    case MemoryRepresentation::Simd256():
      UNREACHABLE();
  }
}
std::tuple<InstructionCode, ImmediateMode> GetLoadOpcodeAndImmediate(
    MemoryRepresentation loaded_rep, RegisterRepresentation result_rep) {
  // NOTE: The meaning of `loaded_rep` = `MemoryRepresentation::AnyTagged()` is
  // we are loading a compressed tagged field, while `result_rep` =
  // `RegisterRepresentation::Tagged()` refers to an uncompressed tagged value.
  switch (loaded_rep) {
    case MemoryRepresentation::Int8():
      DCHECK_EQ(result_rep, RegisterRepresentation::Word32());
      return {kArm64LdrsbW, kLoadStoreImm8};
    case MemoryRepresentation::Uint8():
      DCHECK_EQ(result_rep, RegisterRepresentation::Word32());
      return {kArm64Ldrb, kLoadStoreImm8};
    case MemoryRepresentation::Int16():
      DCHECK_EQ(result_rep, RegisterRepresentation::Word32());
      return {kArm64LdrshW, kLoadStoreImm16};
    case MemoryRepresentation::Uint16():
      DCHECK_EQ(result_rep, RegisterRepresentation::Word32());
      return {kArm64Ldrh, kLoadStoreImm16};
    case MemoryRepresentation::Int32():
    case MemoryRepresentation::Uint32():
      DCHECK_EQ(result_rep, RegisterRepresentation::Word32());
      return {kArm64LdrW, kLoadStoreImm32};
    case MemoryRepresentation::Int64():
    case MemoryRepresentation::Uint64():
      DCHECK_EQ(result_rep, RegisterRepresentation::Word64());
      return {kArm64Ldr, kLoadStoreImm64};
    case MemoryRepresentation::Float16():
      DCHECK_EQ(result_rep, RegisterRepresentation::Float32());
      return {kArm64LdrH, kLoadStoreImm16};
    case MemoryRepresentation::Float32():
      DCHECK_EQ(result_rep, RegisterRepresentation::Float32());
      return {kArm64LdrS, kLoadStoreImm32};
    case MemoryRepresentation::Float64():
      DCHECK_EQ(result_rep, RegisterRepresentation::Float64());
      return {kArm64LdrD, kLoadStoreImm64};
#ifdef V8_COMPRESS_POINTERS
    case MemoryRepresentation::AnyTagged():
    case MemoryRepresentation::TaggedPointer():
      if (result_rep == RegisterRepresentation::Compressed()) {
        return {kArm64LdrW, kLoadStoreImm32};
      }
      DCHECK_EQ(result_rep, RegisterRepresentation::Tagged());
      return {kArm64LdrDecompressTagged, kLoadStoreImm32};
    case MemoryRepresentation::TaggedSigned():
      if (result_rep == RegisterRepresentation::Compressed()) {
        return {kArm64LdrW, kLoadStoreImm32};
      }
      DCHECK_EQ(result_rep, RegisterRepresentation::Tagged());
      return {kArm64LdrDecompressTaggedSigned, kLoadStoreImm32};
#else
    case MemoryRepresentation::AnyTagged():
    case MemoryRepresentation::TaggedPointer():
    case MemoryRepresentation::TaggedSigned():
      return {kArm64Ldr, kLoadStoreImm64};
#endif
    case MemoryRepresentation::AnyUncompressedTagged():
    case MemoryRepresentation::UncompressedTaggedPointer():
    case MemoryRepresentation::UncompressedTaggedSigned():
      DCHECK_EQ(result_rep, RegisterRepresentation::Tagged());
      return {kArm64Ldr, kLoadStoreImm64};
    case MemoryRepresentation::ProtectedPointer():
      CHECK(V8_ENABLE_SANDBOX_BOOL);
      return {kArm64LdrDecompressProtected, kNoImmediate};
    case MemoryRepresentation::IndirectPointer():
      UNREACHABLE();
    case MemoryRepresentation::SandboxedPointer():
      return {kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64};
    case MemoryRepresentation::Simd128():
      return {kArm64LdrQ, kNoImmediate};
    case MemoryRepresentation::Simd256():
      UNREACHABLE();
  }
}
std::tuple<InstructionCode, ImmediateMode> GetLoadOpcodeAndImmediate(
    LoadRepresentation load_rep) {
  switch (load_rep.representation()) {
    case MachineRepresentation::kFloat16:
      return {kArm64LdrH, kLoadStoreImm16};
    case MachineRepresentation::kFloat32:
      return {kArm64LdrS, kLoadStoreImm32};
    case MachineRepresentation::kFloat64:
      return {kArm64LdrD, kLoadStoreImm64};
    case MachineRepresentation::kBit:  // Fall through.
    case MachineRepresentation::kWord8:
      return {load_rep.IsUnsigned()                            ? kArm64Ldrb
              : load_rep.semantic() == MachineSemantic::kInt32 ? kArm64LdrsbW
                                                               : kArm64Ldrsb,
              kLoadStoreImm8};
    case MachineRepresentation::kWord16:
      return {load_rep.IsUnsigned()                            ? kArm64Ldrh
              : load_rep.semantic() == MachineSemantic::kInt32 ? kArm64LdrshW
                                                               : kArm64Ldrsh,
              kLoadStoreImm16};
    case MachineRepresentation::kWord32:
      return {kArm64LdrW, kLoadStoreImm32};
    case MachineRepresentation::kCompressedPointer:  // Fall through.
    case MachineRepresentation::kCompressed:
#ifdef V8_COMPRESS_POINTERS
      return {kArm64LdrW, kLoadStoreImm32};
#else
      UNREACHABLE();
#endif
#ifdef V8_COMPRESS_POINTERS
    case MachineRepresentation::kTaggedSigned:
      return {kArm64LdrDecompressTaggedSigned, kLoadStoreImm32};
    case MachineRepresentation::kTaggedPointer:
    case MachineRepresentation::kTagged:
      return {kArm64LdrDecompressTagged, kLoadStoreImm32};
#else
    case MachineRepresentation::kTaggedSigned:   // Fall through.
    case MachineRepresentation::kTaggedPointer:  // Fall through.
    case MachineRepresentation::kTagged:         // Fall through.
#endif
    case MachineRepresentation::kWord64:
      return {kArm64Ldr, kLoadStoreImm64};
    case MachineRepresentation::kProtectedPointer:
      CHECK(V8_ENABLE_SANDBOX_BOOL);
      return {kArm64LdrDecompressProtected, kNoImmediate};
    case MachineRepresentation::kSandboxedPointer:
      return {kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64};
    case MachineRepresentation::kSimd128:
      return {kArm64LdrQ, kNoImmediate};
    case MachineRepresentation::kSimd256:  // Fall through.
    case MachineRepresentation::kMapWord:  // Fall through.
    case MachineRepresentation::kIndirectPointer:  // Fall through.
    case MachineRepresentation::kFloat16RawBits:   // Fall through.
    case MachineRepresentation::kNone:
      UNREACHABLE();
  }
}
using Result=std::tuple<InstructionCode,ImmediateMode>;
static unsigned checks=0, rejected=0;
template<class F> void check(const char* label, std::optional<Result> expected, F invoke) {
    try {
        auto actual=invoke();
        if (!expected || actual!=*expected) { std::fprintf(stderr,"FAIL result: %s\n",label); std::abort(); }
    } catch (const Rejected&) {
        if (expected) { std::fprintf(stderr,"FAIL rejection: %s\n",label); std::abort(); }
        ++rejected;
    }
    ++checks;
}
int main() {
check("store Int8 paired=False", Result{kArm64Strb, kLoadStoreImm8}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Int8(), false); });
check("store Int8 paired=True", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Int8(), true); });
check("store Uint8 paired=False", Result{kArm64Strb, kLoadStoreImm8}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Uint8(), false); });
check("store Uint8 paired=True", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Uint8(), true); });
check("store Int16 paired=False", Result{kArm64Strh, kLoadStoreImm16}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Int16(), false); });
check("store Int16 paired=True", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Int16(), true); });
check("store Uint16 paired=False", Result{kArm64Strh, kLoadStoreImm16}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Uint16(), false); });
check("store Uint16 paired=True", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Uint16(), true); });
check("store Int32 paired=False", Result{kArm64StrW, kLoadStoreImm32}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Int32(), false); });
check("store Int32 paired=True", Result{kArm64StrWPair, kLoadStoreImm32}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Int32(), true); });
check("store Uint32 paired=False", Result{kArm64StrW, kLoadStoreImm32}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Uint32(), false); });
check("store Uint32 paired=True", Result{kArm64StrWPair, kLoadStoreImm32}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Uint32(), true); });
check("store Int64 paired=False", Result{kArm64Str, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Int64(), false); });
check("store Int64 paired=True", Result{kArm64StrPair, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Int64(), true); });
check("store Uint64 paired=False", Result{kArm64Str, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Uint64(), false); });
check("store Uint64 paired=True", Result{kArm64StrPair, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Uint64(), true); });
check("store Float16 paired=False", Result{kArm64StrH, kLoadStoreImm16}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Float16(), false); });
check("store Float16 paired=True", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Float16(), true); });
check("store Float32 paired=False", Result{kArm64StrS, kLoadStoreImm32}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Float32(), false); });
check("store Float32 paired=True", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Float32(), true); });
check("store Float64 paired=False", Result{kArm64StrD, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Float64(), false); });
check("store Float64 paired=True", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Float64(), true); });
check("store AnyTagged paired=False", COMPRESS_POINTERS_BOOL ? Result{kArm64StrCompressTagged, kLoadStoreImm32} : Result{kArm64StrCompressTagged, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::AnyTagged(), false); });
check("store AnyTagged paired=True", COMPRESS_POINTERS_BOOL ? Result{kArm64StrWPair, kLoadStoreImm32} : Result{kArm64StrPair, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::AnyTagged(), true); });
check("store TaggedPointer paired=False", COMPRESS_POINTERS_BOOL ? Result{kArm64StrCompressTagged, kLoadStoreImm32} : Result{kArm64StrCompressTagged, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::TaggedPointer(), false); });
check("store TaggedPointer paired=True", COMPRESS_POINTERS_BOOL ? Result{kArm64StrWPair, kLoadStoreImm32} : Result{kArm64StrPair, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::TaggedPointer(), true); });
check("store TaggedSigned paired=False", COMPRESS_POINTERS_BOOL ? Result{kArm64StrCompressTagged, kLoadStoreImm32} : Result{kArm64StrCompressTagged, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::TaggedSigned(), false); });
check("store TaggedSigned paired=True", COMPRESS_POINTERS_BOOL ? Result{kArm64StrWPair, kLoadStoreImm32} : Result{kArm64StrPair, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::TaggedSigned(), true); });
check("store AnyUncompressedTagged paired=False", Result{kArm64Str, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::AnyUncompressedTagged(), false); });
check("store AnyUncompressedTagged paired=True", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::AnyUncompressedTagged(), true); });
check("store UncompressedTaggedPointer paired=False", Result{kArm64Str, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedPointer(), false); });
check("store UncompressedTaggedPointer paired=True", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedPointer(), true); });
check("store UncompressedTaggedSigned paired=False", Result{kArm64Str, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedSigned(), false); });
check("store UncompressedTaggedSigned paired=True", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedSigned(), true); });
check("store ProtectedPointer paired=False", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::ProtectedPointer(), false); });
check("store ProtectedPointer paired=True", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::ProtectedPointer(), true); });
check("store IndirectPointer paired=False", Result{kArm64StrIndirectPointer, kLoadStoreImm32}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::IndirectPointer(), false); });
check("store IndirectPointer paired=True", Result{kArm64StrIndirectPointer, kLoadStoreImm32}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::IndirectPointer(), true); });
check("store SandboxedPointer paired=False", Result{kArm64StrEncodeSandboxedPointer, kLoadStoreImm64}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::SandboxedPointer(), false); });
check("store SandboxedPointer paired=True", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::SandboxedPointer(), true); });
check("store Simd128 paired=False", Result{kArm64StrQ, kNoImmediate}, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Simd128(), false); });
check("store Simd128 paired=True", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Simd128(), true); });
check("store Simd256 paired=False", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Simd256(), false); });
check("store Simd256 paired=True", std::nullopt, [] { return GetStoreOpcodeAndImmediate(MemoryRepresentation::Simd256(), true); });
check("load Int8 to Word32", Result{kArm64LdrsbW, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int8(), RegisterRepresentation::Word32()); });
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrsbW, kLoadStoreImm8}
#endif
check("load Int8 to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int8(), RegisterRepresentation::Word64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrsbW, kLoadStoreImm8}
#endif
check("load Int8 to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int8(), RegisterRepresentation::Float32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrsbW, kLoadStoreImm8}
#endif
check("load Int8 to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int8(), RegisterRepresentation::Float64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrsbW, kLoadStoreImm8}
#endif
check("load Int8 to Tagged", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int8(), RegisterRepresentation::Tagged()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrsbW, kLoadStoreImm8}
#endif
check("load Int8 to Compressed", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int8(), RegisterRepresentation::Compressed()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrsbW, kLoadStoreImm8}
#endif
check("load Int8 to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int8(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrsbW, kLoadStoreImm8}
#endif
check("load Int8 to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int8(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
check("load Uint8 to Word32", Result{kArm64Ldrb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint8(), RegisterRepresentation::Word32()); });
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldrb, kLoadStoreImm8}
#endif
check("load Uint8 to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint8(), RegisterRepresentation::Word64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldrb, kLoadStoreImm8}
#endif
check("load Uint8 to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint8(), RegisterRepresentation::Float32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldrb, kLoadStoreImm8}
#endif
check("load Uint8 to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint8(), RegisterRepresentation::Float64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldrb, kLoadStoreImm8}
#endif
check("load Uint8 to Tagged", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint8(), RegisterRepresentation::Tagged()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldrb, kLoadStoreImm8}
#endif
check("load Uint8 to Compressed", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint8(), RegisterRepresentation::Compressed()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldrb, kLoadStoreImm8}
#endif
check("load Uint8 to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint8(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldrb, kLoadStoreImm8}
#endif
check("load Uint8 to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint8(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
check("load Int16 to Word32", Result{kArm64LdrshW, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int16(), RegisterRepresentation::Word32()); });
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrshW, kLoadStoreImm16}
#endif
check("load Int16 to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int16(), RegisterRepresentation::Word64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrshW, kLoadStoreImm16}
#endif
check("load Int16 to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int16(), RegisterRepresentation::Float32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrshW, kLoadStoreImm16}
#endif
check("load Int16 to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int16(), RegisterRepresentation::Float64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrshW, kLoadStoreImm16}
#endif
check("load Int16 to Tagged", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int16(), RegisterRepresentation::Tagged()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrshW, kLoadStoreImm16}
#endif
check("load Int16 to Compressed", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int16(), RegisterRepresentation::Compressed()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrshW, kLoadStoreImm16}
#endif
check("load Int16 to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int16(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrshW, kLoadStoreImm16}
#endif
check("load Int16 to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int16(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
check("load Uint16 to Word32", Result{kArm64Ldrh, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint16(), RegisterRepresentation::Word32()); });
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldrh, kLoadStoreImm16}
#endif
check("load Uint16 to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint16(), RegisterRepresentation::Word64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldrh, kLoadStoreImm16}
#endif
check("load Uint16 to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint16(), RegisterRepresentation::Float32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldrh, kLoadStoreImm16}
#endif
check("load Uint16 to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint16(), RegisterRepresentation::Float64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldrh, kLoadStoreImm16}
#endif
check("load Uint16 to Tagged", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint16(), RegisterRepresentation::Tagged()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldrh, kLoadStoreImm16}
#endif
check("load Uint16 to Compressed", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint16(), RegisterRepresentation::Compressed()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldrh, kLoadStoreImm16}
#endif
check("load Uint16 to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint16(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldrh, kLoadStoreImm16}
#endif
check("load Uint16 to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint16(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
check("load Int32 to Word32", Result{kArm64LdrW, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int32(), RegisterRepresentation::Word32()); });
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrW, kLoadStoreImm32}
#endif
check("load Int32 to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int32(), RegisterRepresentation::Word64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrW, kLoadStoreImm32}
#endif
check("load Int32 to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int32(), RegisterRepresentation::Float32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrW, kLoadStoreImm32}
#endif
check("load Int32 to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int32(), RegisterRepresentation::Float64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrW, kLoadStoreImm32}
#endif
check("load Int32 to Tagged", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int32(), RegisterRepresentation::Tagged()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrW, kLoadStoreImm32}
#endif
check("load Int32 to Compressed", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int32(), RegisterRepresentation::Compressed()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrW, kLoadStoreImm32}
#endif
check("load Int32 to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int32(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrW, kLoadStoreImm32}
#endif
check("load Int32 to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int32(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
check("load Uint32 to Word32", Result{kArm64LdrW, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint32(), RegisterRepresentation::Word32()); });
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrW, kLoadStoreImm32}
#endif
check("load Uint32 to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint32(), RegisterRepresentation::Word64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrW, kLoadStoreImm32}
#endif
check("load Uint32 to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint32(), RegisterRepresentation::Float32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrW, kLoadStoreImm32}
#endif
check("load Uint32 to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint32(), RegisterRepresentation::Float64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrW, kLoadStoreImm32}
#endif
check("load Uint32 to Tagged", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint32(), RegisterRepresentation::Tagged()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrW, kLoadStoreImm32}
#endif
check("load Uint32 to Compressed", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint32(), RegisterRepresentation::Compressed()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrW, kLoadStoreImm32}
#endif
check("load Uint32 to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint32(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrW, kLoadStoreImm32}
#endif
check("load Uint32 to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint32(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load Int64 to Word32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int64(), RegisterRepresentation::Word32()); });
#undef EXPECTED
check("load Int64 to Word64", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int64(), RegisterRepresentation::Word64()); });
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load Int64 to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int64(), RegisterRepresentation::Float32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load Int64 to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int64(), RegisterRepresentation::Float64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load Int64 to Tagged", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int64(), RegisterRepresentation::Tagged()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load Int64 to Compressed", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int64(), RegisterRepresentation::Compressed()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load Int64 to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int64(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load Int64 to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Int64(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load Uint64 to Word32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint64(), RegisterRepresentation::Word32()); });
#undef EXPECTED
check("load Uint64 to Word64", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint64(), RegisterRepresentation::Word64()); });
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load Uint64 to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint64(), RegisterRepresentation::Float32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load Uint64 to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint64(), RegisterRepresentation::Float64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load Uint64 to Tagged", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint64(), RegisterRepresentation::Tagged()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load Uint64 to Compressed", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint64(), RegisterRepresentation::Compressed()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load Uint64 to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint64(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load Uint64 to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Uint64(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrH, kLoadStoreImm16}
#endif
check("load Float16 to Word32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float16(), RegisterRepresentation::Word32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrH, kLoadStoreImm16}
#endif
check("load Float16 to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float16(), RegisterRepresentation::Word64()); });
#undef EXPECTED
check("load Float16 to Float32", Result{kArm64LdrH, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float16(), RegisterRepresentation::Float32()); });
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrH, kLoadStoreImm16}
#endif
check("load Float16 to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float16(), RegisterRepresentation::Float64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrH, kLoadStoreImm16}
#endif
check("load Float16 to Tagged", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float16(), RegisterRepresentation::Tagged()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrH, kLoadStoreImm16}
#endif
check("load Float16 to Compressed", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float16(), RegisterRepresentation::Compressed()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrH, kLoadStoreImm16}
#endif
check("load Float16 to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float16(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrH, kLoadStoreImm16}
#endif
check("load Float16 to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float16(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrS, kLoadStoreImm32}
#endif
check("load Float32 to Word32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float32(), RegisterRepresentation::Word32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrS, kLoadStoreImm32}
#endif
check("load Float32 to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float32(), RegisterRepresentation::Word64()); });
#undef EXPECTED
check("load Float32 to Float32", Result{kArm64LdrS, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float32(), RegisterRepresentation::Float32()); });
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrS, kLoadStoreImm32}
#endif
check("load Float32 to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float32(), RegisterRepresentation::Float64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrS, kLoadStoreImm32}
#endif
check("load Float32 to Tagged", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float32(), RegisterRepresentation::Tagged()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrS, kLoadStoreImm32}
#endif
check("load Float32 to Compressed", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float32(), RegisterRepresentation::Compressed()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrS, kLoadStoreImm32}
#endif
check("load Float32 to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float32(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrS, kLoadStoreImm32}
#endif
check("load Float32 to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float32(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrD, kLoadStoreImm64}
#endif
check("load Float64 to Word32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float64(), RegisterRepresentation::Word32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrD, kLoadStoreImm64}
#endif
check("load Float64 to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float64(), RegisterRepresentation::Word64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrD, kLoadStoreImm64}
#endif
check("load Float64 to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float64(), RegisterRepresentation::Float32()); });
#undef EXPECTED
check("load Float64 to Float64", Result{kArm64LdrD, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float64(), RegisterRepresentation::Float64()); });
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrD, kLoadStoreImm64}
#endif
check("load Float64 to Tagged", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float64(), RegisterRepresentation::Tagged()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrD, kLoadStoreImm64}
#endif
check("load Float64 to Compressed", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float64(), RegisterRepresentation::Compressed()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrD, kLoadStoreImm64}
#endif
check("load Float64 to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float64(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64LdrD, kLoadStoreImm64}
#endif
check("load Float64 to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Float64(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load AnyTagged to Word32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyTagged(), RegisterRepresentation::Word32()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load AnyTagged to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyTagged(), RegisterRepresentation::Word64()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load AnyTagged to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyTagged(), RegisterRepresentation::Float32()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load AnyTagged to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyTagged(), RegisterRepresentation::Float64()); });
#undef EXPECTED
check("load AnyTagged to Tagged", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyTagged(), RegisterRepresentation::Tagged()); });
check("load AnyTagged to Compressed", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrW, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyTagged(), RegisterRepresentation::Compressed()); });
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load AnyTagged to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyTagged(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load AnyTagged to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyTagged(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load TaggedPointer to Word32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedPointer(), RegisterRepresentation::Word32()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load TaggedPointer to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedPointer(), RegisterRepresentation::Word64()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load TaggedPointer to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedPointer(), RegisterRepresentation::Float32()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load TaggedPointer to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedPointer(), RegisterRepresentation::Float64()); });
#undef EXPECTED
check("load TaggedPointer to Tagged", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedPointer(), RegisterRepresentation::Tagged()); });
check("load TaggedPointer to Compressed", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrW, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedPointer(), RegisterRepresentation::Compressed()); });
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load TaggedPointer to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedPointer(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load TaggedPointer to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedPointer(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load TaggedSigned to Word32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedSigned(), RegisterRepresentation::Word32()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load TaggedSigned to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedSigned(), RegisterRepresentation::Word64()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load TaggedSigned to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedSigned(), RegisterRepresentation::Float32()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load TaggedSigned to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedSigned(), RegisterRepresentation::Float64()); });
#undef EXPECTED
check("load TaggedSigned to Tagged", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedSigned(), RegisterRepresentation::Tagged()); });
check("load TaggedSigned to Compressed", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrW, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedSigned(), RegisterRepresentation::Compressed()); });
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load TaggedSigned to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedSigned(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG) && defined(V8_COMPRESS_POINTERS)
#define EXPECTED std::nullopt
#else
#define EXPECTED COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load TaggedSigned to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::TaggedSigned(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load AnyUncompressedTagged to Word32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyUncompressedTagged(), RegisterRepresentation::Word32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load AnyUncompressedTagged to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyUncompressedTagged(), RegisterRepresentation::Word64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load AnyUncompressedTagged to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyUncompressedTagged(), RegisterRepresentation::Float32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load AnyUncompressedTagged to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyUncompressedTagged(), RegisterRepresentation::Float64()); });
#undef EXPECTED
check("load AnyUncompressedTagged to Tagged", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyUncompressedTagged(), RegisterRepresentation::Tagged()); });
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load AnyUncompressedTagged to Compressed", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyUncompressedTagged(), RegisterRepresentation::Compressed()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load AnyUncompressedTagged to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyUncompressedTagged(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load AnyUncompressedTagged to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::AnyUncompressedTagged(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load UncompressedTaggedPointer to Word32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedPointer(), RegisterRepresentation::Word32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load UncompressedTaggedPointer to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedPointer(), RegisterRepresentation::Word64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load UncompressedTaggedPointer to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedPointer(), RegisterRepresentation::Float32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load UncompressedTaggedPointer to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedPointer(), RegisterRepresentation::Float64()); });
#undef EXPECTED
check("load UncompressedTaggedPointer to Tagged", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedPointer(), RegisterRepresentation::Tagged()); });
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load UncompressedTaggedPointer to Compressed", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedPointer(), RegisterRepresentation::Compressed()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load UncompressedTaggedPointer to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedPointer(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load UncompressedTaggedPointer to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedPointer(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load UncompressedTaggedSigned to Word32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedSigned(), RegisterRepresentation::Word32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load UncompressedTaggedSigned to Word64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedSigned(), RegisterRepresentation::Word64()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load UncompressedTaggedSigned to Float32", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedSigned(), RegisterRepresentation::Float32()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load UncompressedTaggedSigned to Float64", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedSigned(), RegisterRepresentation::Float64()); });
#undef EXPECTED
check("load UncompressedTaggedSigned to Tagged", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedSigned(), RegisterRepresentation::Tagged()); });
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load UncompressedTaggedSigned to Compressed", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedSigned(), RegisterRepresentation::Compressed()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load UncompressedTaggedSigned to Simd128", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedSigned(), RegisterRepresentation::Simd128()); });
#undef EXPECTED
#if defined(DEBUG)
#define EXPECTED std::nullopt
#else
#define EXPECTED Result{kArm64Ldr, kLoadStoreImm64}
#endif
check("load UncompressedTaggedSigned to Simd256", EXPECTED, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::UncompressedTaggedSigned(), RegisterRepresentation::Simd256()); });
#undef EXPECTED
check("load ProtectedPointer to Word32", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::ProtectedPointer(), RegisterRepresentation::Word32()); });
check("load ProtectedPointer to Word64", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::ProtectedPointer(), RegisterRepresentation::Word64()); });
check("load ProtectedPointer to Float32", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::ProtectedPointer(), RegisterRepresentation::Float32()); });
check("load ProtectedPointer to Float64", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::ProtectedPointer(), RegisterRepresentation::Float64()); });
check("load ProtectedPointer to Tagged", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::ProtectedPointer(), RegisterRepresentation::Tagged()); });
check("load ProtectedPointer to Compressed", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::ProtectedPointer(), RegisterRepresentation::Compressed()); });
check("load ProtectedPointer to Simd128", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::ProtectedPointer(), RegisterRepresentation::Simd128()); });
check("load ProtectedPointer to Simd256", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::ProtectedPointer(), RegisterRepresentation::Simd256()); });
check("load IndirectPointer to Word32", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::IndirectPointer(), RegisterRepresentation::Word32()); });
check("load IndirectPointer to Word64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::IndirectPointer(), RegisterRepresentation::Word64()); });
check("load IndirectPointer to Float32", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::IndirectPointer(), RegisterRepresentation::Float32()); });
check("load IndirectPointer to Float64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::IndirectPointer(), RegisterRepresentation::Float64()); });
check("load IndirectPointer to Tagged", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::IndirectPointer(), RegisterRepresentation::Tagged()); });
check("load IndirectPointer to Compressed", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::IndirectPointer(), RegisterRepresentation::Compressed()); });
check("load IndirectPointer to Simd128", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::IndirectPointer(), RegisterRepresentation::Simd128()); });
check("load IndirectPointer to Simd256", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::IndirectPointer(), RegisterRepresentation::Simd256()); });
check("load SandboxedPointer to Word32", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::SandboxedPointer(), RegisterRepresentation::Word32()); });
check("load SandboxedPointer to Word64", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::SandboxedPointer(), RegisterRepresentation::Word64()); });
check("load SandboxedPointer to Float32", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::SandboxedPointer(), RegisterRepresentation::Float32()); });
check("load SandboxedPointer to Float64", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::SandboxedPointer(), RegisterRepresentation::Float64()); });
check("load SandboxedPointer to Tagged", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::SandboxedPointer(), RegisterRepresentation::Tagged()); });
check("load SandboxedPointer to Compressed", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::SandboxedPointer(), RegisterRepresentation::Compressed()); });
check("load SandboxedPointer to Simd128", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::SandboxedPointer(), RegisterRepresentation::Simd128()); });
check("load SandboxedPointer to Simd256", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::SandboxedPointer(), RegisterRepresentation::Simd256()); });
check("load Simd128 to Word32", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd128(), RegisterRepresentation::Word32()); });
check("load Simd128 to Word64", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd128(), RegisterRepresentation::Word64()); });
check("load Simd128 to Float32", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd128(), RegisterRepresentation::Float32()); });
check("load Simd128 to Float64", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd128(), RegisterRepresentation::Float64()); });
check("load Simd128 to Tagged", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd128(), RegisterRepresentation::Tagged()); });
check("load Simd128 to Compressed", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd128(), RegisterRepresentation::Compressed()); });
check("load Simd128 to Simd128", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd128(), RegisterRepresentation::Simd128()); });
check("load Simd128 to Simd256", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd128(), RegisterRepresentation::Simd256()); });
check("load Simd256 to Word32", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd256(), RegisterRepresentation::Word32()); });
check("load Simd256 to Word64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd256(), RegisterRepresentation::Word64()); });
check("load Simd256 to Float32", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd256(), RegisterRepresentation::Float32()); });
check("load Simd256 to Float64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd256(), RegisterRepresentation::Float64()); });
check("load Simd256 to Tagged", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd256(), RegisterRepresentation::Tagged()); });
check("load Simd256 to Compressed", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd256(), RegisterRepresentation::Compressed()); });
check("load Simd256 to Simd128", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd256(), RegisterRepresentation::Simd128()); });
check("load Simd256 to Simd256", std::nullopt, [] { return GetLoadOpcodeAndImmediate(MemoryRepresentation::Simd256(), RegisterRepresentation::Simd256()); });
check("legacy None/None", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kNone, MachineSemantic::kNone}); });
check("legacy None/Bool", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kNone, MachineSemantic::kBool}); });
check("legacy None/Int32", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kNone, MachineSemantic::kInt32}); });
check("legacy None/Uint32", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kNone, MachineSemantic::kUint32}); });
check("legacy None/Int64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kNone, MachineSemantic::kInt64}); });
check("legacy None/Uint64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kNone, MachineSemantic::kUint64}); });
check("legacy None/SignedBigInt64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kNone, MachineSemantic::kSignedBigInt64}); });
check("legacy None/UnsignedBigInt64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kNone, MachineSemantic::kUnsignedBigInt64}); });
check("legacy None/Number", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kNone, MachineSemantic::kNumber}); });
check("legacy None/HoleyFloat64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kNone, MachineSemantic::kHoleyFloat64}); });
check("legacy None/Any", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kNone, MachineSemantic::kAny}); });
check("legacy Bit/None", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kBit, MachineSemantic::kNone}); });
check("legacy Bit/Bool", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kBit, MachineSemantic::kBool}); });
check("legacy Bit/Int32", Result{kArm64LdrsbW, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kBit, MachineSemantic::kInt32}); });
check("legacy Bit/Uint32", Result{kArm64Ldrb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kBit, MachineSemantic::kUint32}); });
check("legacy Bit/Int64", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kBit, MachineSemantic::kInt64}); });
check("legacy Bit/Uint64", Result{kArm64Ldrb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kBit, MachineSemantic::kUint64}); });
check("legacy Bit/SignedBigInt64", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kBit, MachineSemantic::kSignedBigInt64}); });
check("legacy Bit/UnsignedBigInt64", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kBit, MachineSemantic::kUnsignedBigInt64}); });
check("legacy Bit/Number", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kBit, MachineSemantic::kNumber}); });
check("legacy Bit/HoleyFloat64", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kBit, MachineSemantic::kHoleyFloat64}); });
check("legacy Bit/Any", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kBit, MachineSemantic::kAny}); });
check("legacy Word8/None", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord8, MachineSemantic::kNone}); });
check("legacy Word8/Bool", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord8, MachineSemantic::kBool}); });
check("legacy Word8/Int32", Result{kArm64LdrsbW, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord8, MachineSemantic::kInt32}); });
check("legacy Word8/Uint32", Result{kArm64Ldrb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord8, MachineSemantic::kUint32}); });
check("legacy Word8/Int64", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord8, MachineSemantic::kInt64}); });
check("legacy Word8/Uint64", Result{kArm64Ldrb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord8, MachineSemantic::kUint64}); });
check("legacy Word8/SignedBigInt64", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord8, MachineSemantic::kSignedBigInt64}); });
check("legacy Word8/UnsignedBigInt64", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord8, MachineSemantic::kUnsignedBigInt64}); });
check("legacy Word8/Number", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord8, MachineSemantic::kNumber}); });
check("legacy Word8/HoleyFloat64", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord8, MachineSemantic::kHoleyFloat64}); });
check("legacy Word8/Any", Result{kArm64Ldrsb, kLoadStoreImm8}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord8, MachineSemantic::kAny}); });
check("legacy Word16/None", Result{kArm64Ldrsh, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord16, MachineSemantic::kNone}); });
check("legacy Word16/Bool", Result{kArm64Ldrsh, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord16, MachineSemantic::kBool}); });
check("legacy Word16/Int32", Result{kArm64LdrshW, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord16, MachineSemantic::kInt32}); });
check("legacy Word16/Uint32", Result{kArm64Ldrh, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord16, MachineSemantic::kUint32}); });
check("legacy Word16/Int64", Result{kArm64Ldrsh, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord16, MachineSemantic::kInt64}); });
check("legacy Word16/Uint64", Result{kArm64Ldrh, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord16, MachineSemantic::kUint64}); });
check("legacy Word16/SignedBigInt64", Result{kArm64Ldrsh, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord16, MachineSemantic::kSignedBigInt64}); });
check("legacy Word16/UnsignedBigInt64", Result{kArm64Ldrsh, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord16, MachineSemantic::kUnsignedBigInt64}); });
check("legacy Word16/Number", Result{kArm64Ldrsh, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord16, MachineSemantic::kNumber}); });
check("legacy Word16/HoleyFloat64", Result{kArm64Ldrsh, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord16, MachineSemantic::kHoleyFloat64}); });
check("legacy Word16/Any", Result{kArm64Ldrsh, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord16, MachineSemantic::kAny}); });
check("legacy Word32/None", Result{kArm64LdrW, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord32, MachineSemantic::kNone}); });
check("legacy Word32/Bool", Result{kArm64LdrW, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord32, MachineSemantic::kBool}); });
check("legacy Word32/Int32", Result{kArm64LdrW, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord32, MachineSemantic::kInt32}); });
check("legacy Word32/Uint32", Result{kArm64LdrW, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord32, MachineSemantic::kUint32}); });
check("legacy Word32/Int64", Result{kArm64LdrW, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord32, MachineSemantic::kInt64}); });
check("legacy Word32/Uint64", Result{kArm64LdrW, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord32, MachineSemantic::kUint64}); });
check("legacy Word32/SignedBigInt64", Result{kArm64LdrW, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord32, MachineSemantic::kSignedBigInt64}); });
check("legacy Word32/UnsignedBigInt64", Result{kArm64LdrW, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord32, MachineSemantic::kUnsignedBigInt64}); });
check("legacy Word32/Number", Result{kArm64LdrW, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord32, MachineSemantic::kNumber}); });
check("legacy Word32/HoleyFloat64", Result{kArm64LdrW, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord32, MachineSemantic::kHoleyFloat64}); });
check("legacy Word32/Any", Result{kArm64LdrW, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord32, MachineSemantic::kAny}); });
check("legacy Word64/None", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord64, MachineSemantic::kNone}); });
check("legacy Word64/Bool", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord64, MachineSemantic::kBool}); });
check("legacy Word64/Int32", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord64, MachineSemantic::kInt32}); });
check("legacy Word64/Uint32", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord64, MachineSemantic::kUint32}); });
check("legacy Word64/Int64", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord64, MachineSemantic::kInt64}); });
check("legacy Word64/Uint64", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord64, MachineSemantic::kUint64}); });
check("legacy Word64/SignedBigInt64", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord64, MachineSemantic::kSignedBigInt64}); });
check("legacy Word64/UnsignedBigInt64", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord64, MachineSemantic::kUnsignedBigInt64}); });
check("legacy Word64/Number", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord64, MachineSemantic::kNumber}); });
check("legacy Word64/HoleyFloat64", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord64, MachineSemantic::kHoleyFloat64}); });
check("legacy Word64/Any", Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kWord64, MachineSemantic::kAny}); });
check("legacy MapWord/None", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kMapWord, MachineSemantic::kNone}); });
check("legacy MapWord/Bool", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kMapWord, MachineSemantic::kBool}); });
check("legacy MapWord/Int32", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kMapWord, MachineSemantic::kInt32}); });
check("legacy MapWord/Uint32", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kMapWord, MachineSemantic::kUint32}); });
check("legacy MapWord/Int64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kMapWord, MachineSemantic::kInt64}); });
check("legacy MapWord/Uint64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kMapWord, MachineSemantic::kUint64}); });
check("legacy MapWord/SignedBigInt64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kMapWord, MachineSemantic::kSignedBigInt64}); });
check("legacy MapWord/UnsignedBigInt64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kMapWord, MachineSemantic::kUnsignedBigInt64}); });
check("legacy MapWord/Number", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kMapWord, MachineSemantic::kNumber}); });
check("legacy MapWord/HoleyFloat64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kMapWord, MachineSemantic::kHoleyFloat64}); });
check("legacy MapWord/Any", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kMapWord, MachineSemantic::kAny}); });
check("legacy TaggedSigned/None", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedSigned, MachineSemantic::kNone}); });
check("legacy TaggedSigned/Bool", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedSigned, MachineSemantic::kBool}); });
check("legacy TaggedSigned/Int32", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedSigned, MachineSemantic::kInt32}); });
check("legacy TaggedSigned/Uint32", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedSigned, MachineSemantic::kUint32}); });
check("legacy TaggedSigned/Int64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedSigned, MachineSemantic::kInt64}); });
check("legacy TaggedSigned/Uint64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedSigned, MachineSemantic::kUint64}); });
check("legacy TaggedSigned/SignedBigInt64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedSigned, MachineSemantic::kSignedBigInt64}); });
check("legacy TaggedSigned/UnsignedBigInt64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedSigned, MachineSemantic::kUnsignedBigInt64}); });
check("legacy TaggedSigned/Number", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedSigned, MachineSemantic::kNumber}); });
check("legacy TaggedSigned/HoleyFloat64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedSigned, MachineSemantic::kHoleyFloat64}); });
check("legacy TaggedSigned/Any", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTaggedSigned, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedSigned, MachineSemantic::kAny}); });
check("legacy TaggedPointer/None", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedPointer, MachineSemantic::kNone}); });
check("legacy TaggedPointer/Bool", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedPointer, MachineSemantic::kBool}); });
check("legacy TaggedPointer/Int32", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedPointer, MachineSemantic::kInt32}); });
check("legacy TaggedPointer/Uint32", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedPointer, MachineSemantic::kUint32}); });
check("legacy TaggedPointer/Int64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedPointer, MachineSemantic::kInt64}); });
check("legacy TaggedPointer/Uint64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedPointer, MachineSemantic::kUint64}); });
check("legacy TaggedPointer/SignedBigInt64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedPointer, MachineSemantic::kSignedBigInt64}); });
check("legacy TaggedPointer/UnsignedBigInt64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedPointer, MachineSemantic::kUnsignedBigInt64}); });
check("legacy TaggedPointer/Number", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedPointer, MachineSemantic::kNumber}); });
check("legacy TaggedPointer/HoleyFloat64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedPointer, MachineSemantic::kHoleyFloat64}); });
check("legacy TaggedPointer/Any", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTaggedPointer, MachineSemantic::kAny}); });
check("legacy Tagged/None", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTagged, MachineSemantic::kNone}); });
check("legacy Tagged/Bool", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTagged, MachineSemantic::kBool}); });
check("legacy Tagged/Int32", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTagged, MachineSemantic::kInt32}); });
check("legacy Tagged/Uint32", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTagged, MachineSemantic::kUint32}); });
check("legacy Tagged/Int64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTagged, MachineSemantic::kInt64}); });
check("legacy Tagged/Uint64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTagged, MachineSemantic::kUint64}); });
check("legacy Tagged/SignedBigInt64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTagged, MachineSemantic::kSignedBigInt64}); });
check("legacy Tagged/UnsignedBigInt64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTagged, MachineSemantic::kUnsignedBigInt64}); });
check("legacy Tagged/Number", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTagged, MachineSemantic::kNumber}); });
check("legacy Tagged/HoleyFloat64", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTagged, MachineSemantic::kHoleyFloat64}); });
check("legacy Tagged/Any", COMPRESS_POINTERS_BOOL ? Result{kArm64LdrDecompressTagged, kLoadStoreImm32} : Result{kArm64Ldr, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kTagged, MachineSemantic::kAny}); });
check("legacy CompressedPointer/None", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressedPointer, MachineSemantic::kNone}); });
check("legacy CompressedPointer/Bool", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressedPointer, MachineSemantic::kBool}); });
check("legacy CompressedPointer/Int32", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressedPointer, MachineSemantic::kInt32}); });
check("legacy CompressedPointer/Uint32", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressedPointer, MachineSemantic::kUint32}); });
check("legacy CompressedPointer/Int64", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressedPointer, MachineSemantic::kInt64}); });
check("legacy CompressedPointer/Uint64", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressedPointer, MachineSemantic::kUint64}); });
check("legacy CompressedPointer/SignedBigInt64", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressedPointer, MachineSemantic::kSignedBigInt64}); });
check("legacy CompressedPointer/UnsignedBigInt64", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressedPointer, MachineSemantic::kUnsignedBigInt64}); });
check("legacy CompressedPointer/Number", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressedPointer, MachineSemantic::kNumber}); });
check("legacy CompressedPointer/HoleyFloat64", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressedPointer, MachineSemantic::kHoleyFloat64}); });
check("legacy CompressedPointer/Any", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressedPointer, MachineSemantic::kAny}); });
check("legacy Compressed/None", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressed, MachineSemantic::kNone}); });
check("legacy Compressed/Bool", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressed, MachineSemantic::kBool}); });
check("legacy Compressed/Int32", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressed, MachineSemantic::kInt32}); });
check("legacy Compressed/Uint32", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressed, MachineSemantic::kUint32}); });
check("legacy Compressed/Int64", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressed, MachineSemantic::kInt64}); });
check("legacy Compressed/Uint64", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressed, MachineSemantic::kUint64}); });
check("legacy Compressed/SignedBigInt64", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressed, MachineSemantic::kSignedBigInt64}); });
check("legacy Compressed/UnsignedBigInt64", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressed, MachineSemantic::kUnsignedBigInt64}); });
check("legacy Compressed/Number", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressed, MachineSemantic::kNumber}); });
check("legacy Compressed/HoleyFloat64", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressed, MachineSemantic::kHoleyFloat64}); });
check("legacy Compressed/Any", COMPRESS_POINTERS_BOOL ? std::optional<Result>{Result{kArm64LdrW, kLoadStoreImm32}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kCompressed, MachineSemantic::kAny}); });
check("legacy ProtectedPointer/None", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kProtectedPointer, MachineSemantic::kNone}); });
check("legacy ProtectedPointer/Bool", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kProtectedPointer, MachineSemantic::kBool}); });
check("legacy ProtectedPointer/Int32", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kProtectedPointer, MachineSemantic::kInt32}); });
check("legacy ProtectedPointer/Uint32", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kProtectedPointer, MachineSemantic::kUint32}); });
check("legacy ProtectedPointer/Int64", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kProtectedPointer, MachineSemantic::kInt64}); });
check("legacy ProtectedPointer/Uint64", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kProtectedPointer, MachineSemantic::kUint64}); });
check("legacy ProtectedPointer/SignedBigInt64", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kProtectedPointer, MachineSemantic::kSignedBigInt64}); });
check("legacy ProtectedPointer/UnsignedBigInt64", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kProtectedPointer, MachineSemantic::kUnsignedBigInt64}); });
check("legacy ProtectedPointer/Number", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kProtectedPointer, MachineSemantic::kNumber}); });
check("legacy ProtectedPointer/HoleyFloat64", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kProtectedPointer, MachineSemantic::kHoleyFloat64}); });
check("legacy ProtectedPointer/Any", SANDBOX ? std::optional<Result>{Result{kArm64LdrDecompressProtected, kNoImmediate}} : std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kProtectedPointer, MachineSemantic::kAny}); });
check("legacy IndirectPointer/None", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kIndirectPointer, MachineSemantic::kNone}); });
check("legacy IndirectPointer/Bool", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kIndirectPointer, MachineSemantic::kBool}); });
check("legacy IndirectPointer/Int32", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kIndirectPointer, MachineSemantic::kInt32}); });
check("legacy IndirectPointer/Uint32", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kIndirectPointer, MachineSemantic::kUint32}); });
check("legacy IndirectPointer/Int64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kIndirectPointer, MachineSemantic::kInt64}); });
check("legacy IndirectPointer/Uint64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kIndirectPointer, MachineSemantic::kUint64}); });
check("legacy IndirectPointer/SignedBigInt64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kIndirectPointer, MachineSemantic::kSignedBigInt64}); });
check("legacy IndirectPointer/UnsignedBigInt64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kIndirectPointer, MachineSemantic::kUnsignedBigInt64}); });
check("legacy IndirectPointer/Number", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kIndirectPointer, MachineSemantic::kNumber}); });
check("legacy IndirectPointer/HoleyFloat64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kIndirectPointer, MachineSemantic::kHoleyFloat64}); });
check("legacy IndirectPointer/Any", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kIndirectPointer, MachineSemantic::kAny}); });
check("legacy SandboxedPointer/None", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSandboxedPointer, MachineSemantic::kNone}); });
check("legacy SandboxedPointer/Bool", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSandboxedPointer, MachineSemantic::kBool}); });
check("legacy SandboxedPointer/Int32", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSandboxedPointer, MachineSemantic::kInt32}); });
check("legacy SandboxedPointer/Uint32", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSandboxedPointer, MachineSemantic::kUint32}); });
check("legacy SandboxedPointer/Int64", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSandboxedPointer, MachineSemantic::kInt64}); });
check("legacy SandboxedPointer/Uint64", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSandboxedPointer, MachineSemantic::kUint64}); });
check("legacy SandboxedPointer/SignedBigInt64", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSandboxedPointer, MachineSemantic::kSignedBigInt64}); });
check("legacy SandboxedPointer/UnsignedBigInt64", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSandboxedPointer, MachineSemantic::kUnsignedBigInt64}); });
check("legacy SandboxedPointer/Number", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSandboxedPointer, MachineSemantic::kNumber}); });
check("legacy SandboxedPointer/HoleyFloat64", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSandboxedPointer, MachineSemantic::kHoleyFloat64}); });
check("legacy SandboxedPointer/Any", Result{kArm64LdrDecodeSandboxedPointer, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSandboxedPointer, MachineSemantic::kAny}); });
check("legacy Float16RawBits/None", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16RawBits, MachineSemantic::kNone}); });
check("legacy Float16RawBits/Bool", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16RawBits, MachineSemantic::kBool}); });
check("legacy Float16RawBits/Int32", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16RawBits, MachineSemantic::kInt32}); });
check("legacy Float16RawBits/Uint32", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16RawBits, MachineSemantic::kUint32}); });
check("legacy Float16RawBits/Int64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16RawBits, MachineSemantic::kInt64}); });
check("legacy Float16RawBits/Uint64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16RawBits, MachineSemantic::kUint64}); });
check("legacy Float16RawBits/SignedBigInt64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16RawBits, MachineSemantic::kSignedBigInt64}); });
check("legacy Float16RawBits/UnsignedBigInt64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16RawBits, MachineSemantic::kUnsignedBigInt64}); });
check("legacy Float16RawBits/Number", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16RawBits, MachineSemantic::kNumber}); });
check("legacy Float16RawBits/HoleyFloat64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16RawBits, MachineSemantic::kHoleyFloat64}); });
check("legacy Float16RawBits/Any", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16RawBits, MachineSemantic::kAny}); });
check("legacy Float16/None", Result{kArm64LdrH, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16, MachineSemantic::kNone}); });
check("legacy Float16/Bool", Result{kArm64LdrH, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16, MachineSemantic::kBool}); });
check("legacy Float16/Int32", Result{kArm64LdrH, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16, MachineSemantic::kInt32}); });
check("legacy Float16/Uint32", Result{kArm64LdrH, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16, MachineSemantic::kUint32}); });
check("legacy Float16/Int64", Result{kArm64LdrH, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16, MachineSemantic::kInt64}); });
check("legacy Float16/Uint64", Result{kArm64LdrH, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16, MachineSemantic::kUint64}); });
check("legacy Float16/SignedBigInt64", Result{kArm64LdrH, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16, MachineSemantic::kSignedBigInt64}); });
check("legacy Float16/UnsignedBigInt64", Result{kArm64LdrH, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16, MachineSemantic::kUnsignedBigInt64}); });
check("legacy Float16/Number", Result{kArm64LdrH, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16, MachineSemantic::kNumber}); });
check("legacy Float16/HoleyFloat64", Result{kArm64LdrH, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16, MachineSemantic::kHoleyFloat64}); });
check("legacy Float16/Any", Result{kArm64LdrH, kLoadStoreImm16}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat16, MachineSemantic::kAny}); });
check("legacy Float32/None", Result{kArm64LdrS, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat32, MachineSemantic::kNone}); });
check("legacy Float32/Bool", Result{kArm64LdrS, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat32, MachineSemantic::kBool}); });
check("legacy Float32/Int32", Result{kArm64LdrS, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat32, MachineSemantic::kInt32}); });
check("legacy Float32/Uint32", Result{kArm64LdrS, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat32, MachineSemantic::kUint32}); });
check("legacy Float32/Int64", Result{kArm64LdrS, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat32, MachineSemantic::kInt64}); });
check("legacy Float32/Uint64", Result{kArm64LdrS, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat32, MachineSemantic::kUint64}); });
check("legacy Float32/SignedBigInt64", Result{kArm64LdrS, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat32, MachineSemantic::kSignedBigInt64}); });
check("legacy Float32/UnsignedBigInt64", Result{kArm64LdrS, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat32, MachineSemantic::kUnsignedBigInt64}); });
check("legacy Float32/Number", Result{kArm64LdrS, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat32, MachineSemantic::kNumber}); });
check("legacy Float32/HoleyFloat64", Result{kArm64LdrS, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat32, MachineSemantic::kHoleyFloat64}); });
check("legacy Float32/Any", Result{kArm64LdrS, kLoadStoreImm32}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat32, MachineSemantic::kAny}); });
check("legacy Float64/None", Result{kArm64LdrD, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat64, MachineSemantic::kNone}); });
check("legacy Float64/Bool", Result{kArm64LdrD, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat64, MachineSemantic::kBool}); });
check("legacy Float64/Int32", Result{kArm64LdrD, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat64, MachineSemantic::kInt32}); });
check("legacy Float64/Uint32", Result{kArm64LdrD, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat64, MachineSemantic::kUint32}); });
check("legacy Float64/Int64", Result{kArm64LdrD, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat64, MachineSemantic::kInt64}); });
check("legacy Float64/Uint64", Result{kArm64LdrD, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat64, MachineSemantic::kUint64}); });
check("legacy Float64/SignedBigInt64", Result{kArm64LdrD, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat64, MachineSemantic::kSignedBigInt64}); });
check("legacy Float64/UnsignedBigInt64", Result{kArm64LdrD, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat64, MachineSemantic::kUnsignedBigInt64}); });
check("legacy Float64/Number", Result{kArm64LdrD, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat64, MachineSemantic::kNumber}); });
check("legacy Float64/HoleyFloat64", Result{kArm64LdrD, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat64, MachineSemantic::kHoleyFloat64}); });
check("legacy Float64/Any", Result{kArm64LdrD, kLoadStoreImm64}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kFloat64, MachineSemantic::kAny}); });
check("legacy Simd128/None", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd128, MachineSemantic::kNone}); });
check("legacy Simd128/Bool", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd128, MachineSemantic::kBool}); });
check("legacy Simd128/Int32", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd128, MachineSemantic::kInt32}); });
check("legacy Simd128/Uint32", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd128, MachineSemantic::kUint32}); });
check("legacy Simd128/Int64", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd128, MachineSemantic::kInt64}); });
check("legacy Simd128/Uint64", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd128, MachineSemantic::kUint64}); });
check("legacy Simd128/SignedBigInt64", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd128, MachineSemantic::kSignedBigInt64}); });
check("legacy Simd128/UnsignedBigInt64", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd128, MachineSemantic::kUnsignedBigInt64}); });
check("legacy Simd128/Number", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd128, MachineSemantic::kNumber}); });
check("legacy Simd128/HoleyFloat64", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd128, MachineSemantic::kHoleyFloat64}); });
check("legacy Simd128/Any", Result{kArm64LdrQ, kNoImmediate}, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd128, MachineSemantic::kAny}); });
check("legacy Simd256/None", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd256, MachineSemantic::kNone}); });
check("legacy Simd256/Bool", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd256, MachineSemantic::kBool}); });
check("legacy Simd256/Int32", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd256, MachineSemantic::kInt32}); });
check("legacy Simd256/Uint32", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd256, MachineSemantic::kUint32}); });
check("legacy Simd256/Int64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd256, MachineSemantic::kInt64}); });
check("legacy Simd256/Uint64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd256, MachineSemantic::kUint64}); });
check("legacy Simd256/SignedBigInt64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd256, MachineSemantic::kSignedBigInt64}); });
check("legacy Simd256/UnsignedBigInt64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd256, MachineSemantic::kUnsignedBigInt64}); });
check("legacy Simd256/Number", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd256, MachineSemantic::kNumber}); });
check("legacy Simd256/HoleyFloat64", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd256, MachineSemantic::kHoleyFloat64}); });
check("legacy Simd256/Any", std::nullopt, [] { return GetLoadOpcodeAndImmediate(LoadRepresentation{MachineRepresentation::kSimd256, MachineSemantic::kAny}); });
std::printf("PASS: %u selector cases (%u rejected)\n", checks, rejected);
}
