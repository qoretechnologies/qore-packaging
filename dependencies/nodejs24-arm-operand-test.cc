// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "src/regexp/arm64/regexp-macro-assembler-arm64.h"
#include "src/codegen/arm64/assembler-arm64-inl.h"
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>

using namespace v8::internal;
static size_t checks = 0;
static void require(bool ok, const char* label) {
  ++checks;
  if (!ok) {
    std::fprintf(stderr, "FAIL: %s at %zu\n", label, checks);
    std::exit(1);
  }
}
static void immediate(const Operand& op, int64_t expected) {
  require(op.IsImmediate(), "immediate tag");
  require(!op.IsShiftedRegister(), "immediate excludes shifted register");
  require(!op.IsExtendedRegister(), "immediate excludes extended register");
  require(op.ImmediateValue() == expected, "immediate value");
  require(op.IsZero() == (expected == 0), "zero classification");
}
int main() {
  std::array<int64_t, 11> edges{{std::numeric_limits<int64_t>::min(), -4294967296LL,
    -2147483649LL, -2147483648LL, -1, 0, 1, 2147483647LL, 2147483648LL,
    4294967295LL, std::numeric_limits<int64_t>::max()}};
  for (int64_t value : edges) {
    Operand a(value);
    immediate(a, value);
    Operand b = a;
    immediate(b, value);
    for (Shift shift : {LSL, LSR, ASR, ROR}) {
      for (unsigned amount : {0U, 1U, 31U, 32U, 63U}) {
        b = Operand(x7, shift, amount);
        require(!b.IsImmediate(), "shifted excludes immediate");
        require(b.IsShiftedRegister(), "shifted tag");
        require(!b.IsExtendedRegister(), "shifted excludes extended");
        require(b.reg() == x7 && b.shift() == shift && b.shift_amount() == amount,
                "shifted fields");
        b = a;
        immediate(b, value);
      }
    }
    for (Extend extend : {UXTB, UXTH, UXTW, UXTX, SXTB, SXTH, SXTW, SXTX}) {
      for (unsigned amount : {0U, 1U, 4U}) {
        b = Operand(x9, extend, amount);
        require(!b.IsImmediate(), "extended excludes immediate");
        require(!b.IsShiftedRegister(), "extended excludes shifted");
        require(b.IsExtendedRegister(), "extended tag");
        require(b.reg() == x9 && b.extend() == extend && b.shift_amount() == amount,
                "extended fields");
        b = a;
        immediate(b, value);
      }
    }
  }
  // The moved call-site argument is the int specialization, including zero.
  for (int value : {std::numeric_limits<int>::min(), -1, 0, 1, std::numeric_limits<int>::max()}) {
    immediate(Operand(value), value);
  }
  std::printf("PASS: %zu actual ARM64 Operand checks\n", checks);
}
