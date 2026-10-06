// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Extracted unchanged V8 enum switches with typed output adapters.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <tuple>
#include <utility>
void require(bool value) { if (!value) { std::abort(); } }
#define FOREACH_SIMD_128_LOAD_TRANSFORM_OPCODE(V) \
  V(8x8S)                                         \
  V(8x8U)                                         \
  V(16x4S)                                        \
  V(16x4U)                                        \
  V(32x2S)                                        \
  V(32x2U)                                        \
  V(8Splat)                                       \
  V(16Splat)                                      \
  V(32Splat)                                      \
  V(64Splat)                                      \
  V(32Zero)                                       \
  V(64Zero)
#define FOREACH_SIMD_256_LOAD_TRANSFORM_OPCODE(V) \
  V(8x16S)                                        \
  V(8x16U)                                        \
  V(8x8U)                                         \
  V(16x8S)                                        \
  V(16x8U)                                        \
  V(32x4S)                                        \
  V(32x4U)                                        \
  V(8Splat)                                       \
  V(16Splat)                                      \
  V(32Splat)                                      \
  V(64Splat)
#define ASSERT_CONDITION(V) \
  V(Equal)                  \
  V(NotEqual)               \
  V(LessThan)               \
  V(LessThanEqual)          \
  V(GreaterThan)            \
  V(GreaterThanEqual)       \
  V(UnsignedLessThan)       \
  V(UnsignedLessThanEqual)  \
  V(UnsignedGreaterThan)    \
  V(UnsignedGreaterThanEqual)
#define IEEE_754_UNARY_LIST(V) \
  V(MathAcos, acos, Acos)      \
  V(MathAcosh, acosh, Acosh)   \
  V(MathAsin, asin, Asin)      \
  V(MathAsinh, asinh, Asinh)   \
  V(MathAtan, atan, Atan)      \
  V(MathAtanh, atanh, Atanh)   \
  V(MathCbrt, cbrt, Cbrt)      \
  V(MathCos, cos, Cos)         \
  V(MathCosh, cosh, Cosh)      \
  V(MathExp, exp, Exp)         \
  V(MathExpm1, expm1, Expm1)   \
  V(MathLog, log, Log)         \
  V(MathLog1p, log1p, Log1p)   \
  V(MathLog10, log10, Log10)   \
  V(MathLog2, log2, Log2)      \
  V(MathSin, sin, Sin)         \
  V(MathSinh, sinh, Sinh)      \
  V(MathTan, tan, Tan)         \
  V(MathTanh, tanh, Tanh)
struct Simd128LoadTransformOp {
  enum class TransformKind : uint8_t {
#define DEFINE_KIND(kind) k##kind,
    FOREACH_SIMD_128_LOAD_TRANSFORM_OPCODE(DEFINE_KIND)
#undef DEFINE_KIND
  };
TransformKind transform_kind;
};
struct Simd256LoadTransformOp {
  enum class TransformKind : uint8_t {
#define DEFINE_KIND(kind) k##kind,
    FOREACH_SIMD_256_LOAD_TRANSFORM_OPCODE(DEFINE_KIND)
#undef DEFINE_KIND
  };
TransformKind transform_kind;
};
namespace maglev {
enum class AssertCondition {
#define D(Name) k##Name,
  ASSERT_CONDITION(D)
#undef D
};
struct Float64Ieee754Unary {
  enum class Ieee754Function : uint8_t {
#define DECL_ENUM(MathName, ExtName, EnumName) k##EnumName,
    IEEE_754_UNARY_LIST(DECL_ENUM)
#undef DECL_ENUM
  };
Ieee754Function mode; auto ieee_function() const { return mode; }
};
}
struct ComparisonOp {
  enum class Kind : uint8_t {
    kEqual,
    kSignedLessThan,
    kSignedLessThanOrEqual,
    kUnsignedLessThan,
    kUnsignedLessThanOrEqual
  };
};
struct FloatUnaryOp {
  enum class Kind : uint8_t {
    kAbs,
    kNegate,
    kSilenceNaN,
    kRoundDown,      // round towards -infinity
    kRoundUp,        // round towards +infinity
    kRoundToZero,    // round towards 0
    kRoundTiesEven,  // break ties by rounding towards the next even number
    kLog,
    kLog2,
    kLog10,
    kLog1p,
    kSqrt,
    kCbrt,
    kExp,
    kExpm1,
    kSin,
    kCos,
    kSinh,
    kCosh,
    kAcos,
    kAsin,
    kAsinh,
    kAcosh,
    kTan,
    kTanh,
    kAtan,
    kAtanh,
  };
};
enum class ShiftKind { kNormal, kShiftOutZeros };
struct ShiftOp {
  enum class Kind : uint8_t {
    kShiftRightArithmeticShiftOutZeros,
    kShiftRightArithmetic,
    kShiftRightLogical,
    kShiftLeft,
    kRotateRight,
    kRotateLeft
  };
};
enum ArchOpcode {
kX64Movsd=1,
kX64Movss=2,
kX64S128Load16Splat=3,
kX64S128Load16x4S=4,
kX64S128Load16x4U=5,
kX64S128Load32Splat=6,
kX64S128Load32x2S=7,
kX64S128Load32x2U=8,
kX64S128Load64Splat=9,
kX64S128Load8Splat=10,
kX64S128Load8x8S=11,
kX64S128Load8x8U=12,
kX64S256Load16Splat=13,
kX64S256Load16x8S=14,
kX64S256Load16x8U=15,
kX64S256Load32Splat=16,
kX64S256Load32x4S=17,
kX64S256Load32x4U=18,
kX64S256Load64Splat=19,
kX64S256Load8Splat=20,
kX64S256Load8x16S=21,
kX64S256Load8x16U=22,
kX64S256Load8x8U=23
};
ShiftKind ShiftKindOf(const ShiftKind* op) { return *op; }
__attribute__((noinline)) ArchOpcode Simd128(Simd128LoadTransformOp op) {
  ArchOpcode opcode;
  switch (op.transform_kind) {
    case Simd128LoadTransformOp::TransformKind::k8x8S:
      opcode = kX64S128Load8x8S;
      break;
    case Simd128LoadTransformOp::TransformKind::k8x8U:
      opcode = kX64S128Load8x8U;
      break;
    case Simd128LoadTransformOp::TransformKind::k16x4S:
      opcode = kX64S128Load16x4S;
      break;
    case Simd128LoadTransformOp::TransformKind::k16x4U:
      opcode = kX64S128Load16x4U;
      break;
    case Simd128LoadTransformOp::TransformKind::k32x2S:
      opcode = kX64S128Load32x2S;
      break;
    case Simd128LoadTransformOp::TransformKind::k32x2U:
      opcode = kX64S128Load32x2U;
      break;
    case Simd128LoadTransformOp::TransformKind::k8Splat:
      opcode = kX64S128Load8Splat;
      break;
    case Simd128LoadTransformOp::TransformKind::k16Splat:
      opcode = kX64S128Load16Splat;
      break;
    case Simd128LoadTransformOp::TransformKind::k32Splat:
      opcode = kX64S128Load32Splat;
      break;
    case Simd128LoadTransformOp::TransformKind::k64Splat:
      opcode = kX64S128Load64Splat;
      break;
    case Simd128LoadTransformOp::TransformKind::k32Zero:
      opcode = kX64Movss;
      break;
    case Simd128LoadTransformOp::TransformKind::k64Zero:
      opcode = kX64Movsd;
      break;
  }
return opcode;
}
__attribute__((noinline)) ArchOpcode Simd256(Simd256LoadTransformOp op) {
  ArchOpcode opcode;
  switch (op.transform_kind) {
    case Simd256LoadTransformOp::TransformKind::k8x16S:
      opcode = kX64S256Load8x16S;
      break;
    case Simd256LoadTransformOp::TransformKind::k8x16U:
      opcode = kX64S256Load8x16U;
      break;
    case Simd256LoadTransformOp::TransformKind::k8x8U:
      opcode = kX64S256Load8x8U;
      break;
    case Simd256LoadTransformOp::TransformKind::k16x8S:
      opcode = kX64S256Load16x8S;
      break;
    case Simd256LoadTransformOp::TransformKind::k16x8U:
      opcode = kX64S256Load16x8U;
      break;
    case Simd256LoadTransformOp::TransformKind::k32x4S:
      opcode = kX64S256Load32x4S;
      break;
    case Simd256LoadTransformOp::TransformKind::k32x4U:
      opcode = kX64S256Load32x4U;
      break;
    case Simd256LoadTransformOp::TransformKind::k8Splat:
      opcode = kX64S256Load8Splat;
      break;
    case Simd256LoadTransformOp::TransformKind::k16Splat:
      opcode = kX64S256Load16Splat;
      break;
    case Simd256LoadTransformOp::TransformKind::k32Splat:
      opcode = kX64S256Load32Splat;
      break;
    case Simd256LoadTransformOp::TransformKind::k64Splat:
      opcode = kX64S256Load64Splat;
      break;
  }
return opcode;
}
__attribute__((noinline)) auto Compare(maglev::AssertCondition condition, bool* negate_result) {
    ComparisonOp::Kind kind;
    bool swap_inputs = false;
    switch (condition) {
      case maglev::AssertCondition::kEqual:
        kind = ComparisonOp::Kind::kEqual;
        break;
      case maglev::AssertCondition::kNotEqual:
        kind = ComparisonOp::Kind::kEqual;
        *negate_result = true;
        break;
      case maglev::AssertCondition::kLessThan:
        kind = ComparisonOp::Kind::kSignedLessThan;
        break;
      case maglev::AssertCondition::kLessThanEqual:
        kind = ComparisonOp::Kind::kSignedLessThanOrEqual;
        break;
      case maglev::AssertCondition::kGreaterThan:
        kind = ComparisonOp::Kind::kSignedLessThan;
        swap_inputs = true;
        break;
      case maglev::AssertCondition::kGreaterThanEqual:
        kind = ComparisonOp::Kind::kSignedLessThanOrEqual;
        swap_inputs = true;
        break;
      case maglev::AssertCondition::kUnsignedLessThan:
        kind = ComparisonOp::Kind::kUnsignedLessThan;
        break;
      case maglev::AssertCondition::kUnsignedLessThanEqual:
        kind = ComparisonOp::Kind::kUnsignedLessThanOrEqual;
        break;
      case maglev::AssertCondition::kUnsignedGreaterThan:
        kind = ComparisonOp::Kind::kUnsignedLessThan;
        swap_inputs = true;
        break;
      case maglev::AssertCondition::kUnsignedGreaterThanEqual:
        kind = ComparisonOp::Kind::kUnsignedLessThanOrEqual;
        swap_inputs = true;
        break;
    }
return std::pair{kind,swap_inputs};
}
__attribute__((noinline)) auto Unary(maglev::Float64Ieee754Unary* node) {
    FloatUnaryOp::Kind kind;
    switch (node->ieee_function()) {
#define CASE(MathName, ExpName, EnumName)                         \
  case maglev::Float64Ieee754Unary::Ieee754Function::k##EnumName: \
    kind = FloatUnaryOp::Kind::k##EnumName;                       \
    break;
      IEEE_754_UNARY_LIST(CASE)
#undef CASE
    }
return kind;
}
__attribute__((noinline)) auto Shift(const ShiftKind* op) {
      ShiftOp::Kind kind;
      switch (ShiftKindOf(op)) {
        case ShiftKind::kShiftOutZeros:
          kind = ShiftOp::Kind::kShiftRightArithmeticShiftOutZeros;
          break;
        case ShiftKind::kNormal:
          kind = ShiftOp::Kind::kShiftRightArithmetic;
          break;
      }
return kind;
}

bool evaluate(ComparisonOp::Kind k, int32_t left, int32_t right) {
 switch(k) {
 case ComparisonOp::Kind::kEqual: return left==right;
 case ComparisonOp::Kind::kSignedLessThan: return left<right;
 case ComparisonOp::Kind::kSignedLessThanOrEqual: return left<=right;
 case ComparisonOp::Kind::kUnsignedLessThan: return uint32_t(left)<uint32_t(right);
 case ComparisonOp::Kind::kUnsignedLessThanOrEqual: return uint32_t(left)<=uint32_t(right);
 }
 std::abort();
}
bool expected(unsigned mode,int32_t a,int32_t b) {
 switch(mode) {
 case 0:return a==b; case 1:return a!=b; case 2:return a<b; case 3:return a<=b;
 case 4:return a>b; case 5:return a>=b; case 6:return uint32_t(a)<uint32_t(b);
 case 7:return uint32_t(a)<=uint32_t(b); case 8:return uint32_t(a)>uint32_t(b);
 case 9:return uint32_t(a)>=uint32_t(b); default:std::abort();
 }
}
int main() {
 using S128=Simd128LoadTransformOp::TransformKind; using S256=Simd256LoadTransformOp::TransformKind;
 const std::array modes128{S128::k8x8S,S128::k8x8U,S128::k16x4S,S128::k16x4U,S128::k32x2S,S128::k32x2U,S128::k8Splat,S128::k16Splat,S128::k32Splat,S128::k64Splat,S128::k32Zero,S128::k64Zero};
 const std::array expected128{kX64S128Load8x8S,kX64S128Load8x8U,kX64S128Load16x4S,kX64S128Load16x4U,kX64S128Load32x2S,kX64S128Load32x2U,kX64S128Load8Splat,kX64S128Load16Splat,kX64S128Load32Splat,kX64S128Load64Splat,kX64Movss,kX64Movsd};
 const std::array modes256{S256::k8x16S,S256::k8x16U,S256::k8x8U,S256::k16x8S,S256::k16x8U,S256::k32x4S,S256::k32x4U,S256::k8Splat,S256::k16Splat,S256::k32Splat,S256::k64Splat};
 const std::array expected256{kX64S256Load8x16S,kX64S256Load8x16U,kX64S256Load8x8U,kX64S256Load16x8S,kX64S256Load16x8U,kX64S256Load32x4S,kX64S256Load32x4U,kX64S256Load8Splat,kX64S256Load16Splat,kX64S256Load32Splat,kX64S256Load64Splat};
 using A=maglev::AssertCondition; const std::array assertions{A::kEqual,A::kNotEqual,A::kLessThan,A::kLessThanEqual,A::kGreaterThan,A::kGreaterThanEqual,A::kUnsignedLessThan,A::kUnsignedLessThanEqual,A::kUnsignedGreaterThan,A::kUnsignedGreaterThanEqual};
 using I=maglev::Float64Ieee754Unary::Ieee754Function; using F=FloatUnaryOp::Kind;
 const std::array unary{
#define ITEM(MathName,ExpName,EnumName) std::pair{I::k##EnumName,F::k##EnumName},
 IEEE_754_UNARY_LIST(ITEM)
#undef ITEM
 };
 const std::array<int32_t,7> boundaries{std::numeric_limits<int32_t>::min(),-65536,-1,0,1,65536,std::numeric_limits<int32_t>::max()};
 unsigned checks=0;
 for(unsigned repeat=0;repeat<1000;++repeat) {
  for(unsigned i=0;i<modes128.size();++i) { require(Simd128({modes128[i]})==expected128[i]);++checks; }
  for(unsigned i=0;i<modes256.size();++i) { require(Simd256({modes256[i]})==expected256[i]);++checks; }
  for(unsigned i=0;i<assertions.size();++i) {
   bool negate=false;auto[kind,swap]=Compare(assertions[i],&negate);
   require(negate==(i==1));require(swap==(i==4||i==5||i==8||i==9));
   for(int32_t left:boundaries) { for(int32_t right:boundaries) {
    int32_t a=left,b=right;if(swap) { std::swap(a,b); }
    require((evaluate(kind,a,b)!=negate)==expected(i,left,right));++checks;
   } }
  }
  for(auto[mode,kind]:unary) { maglev::Float64Ieee754Unary node{mode};require(Unary(&node)==kind);++checks; }
  for(auto mode:{ShiftKind::kNormal,ShiftKind::kShiftOutZeros}) { require(Shift(&mode)==(mode==ShiftKind::kNormal?ShiftOp::Kind::kShiftRightArithmetic:ShiftOp::Kind::kShiftRightArithmeticShiftOutZeros));++checks; }
 }
 std::printf("PASS: %u instruction, comparison, unary and shift dispatch checks\n",checks);
}
