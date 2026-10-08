// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// V8 declarations and method below are unchanged BSD-licensed source extracts.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <utility>
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
struct Simd128ExtractLaneOp {
  enum class Kind : uint8_t {
    kI8x16S,
    kI8x16U,
    kI16x8S,
    kI16x8U,
    kI32x4,
    kI64x2,
    kF16x8,
    kF32x4,
    kF64x2,
  };
  static MachineRepresentation element_rep(Kind kind) {
    switch (kind) {
      case Kind::kI8x16S:
      case Kind::kI8x16U:
        return MachineRepresentation::kWord8;
      case Kind::kI16x8S:
      case Kind::kI16x8U:
        return MachineRepresentation::kWord16;
      case Kind::kI32x4:
        return MachineRepresentation::kWord32;
      case Kind::kI64x2:
        return MachineRepresentation::kWord64;
      case Kind::kF16x8:
      case Kind::kF32x4:
        return MachineRepresentation::kFloat32;
      case Kind::kF64x2:
        return MachineRepresentation::kFloat64;
    }
  }
};
__attribute__((noinline)) MachineRepresentation invoke(Simd128ExtractLaneOp::Kind kind) {
  return Simd128ExtractLaneOp::element_rep(kind);
}
int main() {
  using K = Simd128ExtractLaneOp::Kind;
  using M = MachineRepresentation;
  const std::array cases{
    std::pair{K::kI8x16S, M::kWord8},
    std::pair{K::kI8x16U, M::kWord8},
    std::pair{K::kI16x8S, M::kWord16},
    std::pair{K::kI16x8U, M::kWord16},
    std::pair{K::kI32x4, M::kWord32},
    std::pair{K::kI64x2, M::kWord64},
    std::pair{K::kF16x8, M::kFloat32},
    std::pair{K::kF32x4, M::kFloat32},
    std::pair{K::kF64x2, M::kFloat64}
  };
  unsigned checks = 0;
  for (const auto& [kind, expected] : cases) {
    if (invoke(kind) != expected) {
      std::fprintf(stderr, "FAIL: kind %u\n", static_cast<unsigned>(kind));
      return 1;
    }
    ++checks;
  }
  std::printf("PASS: %u declared SIMD lane kinds map to their correct machine representations\n", checks);
}
