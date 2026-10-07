// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#pragma once
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <optional>
#include <set>
#include <vector>
inline void require(bool value) {if (!value) {std::abort();}}
#ifdef DEBUG
#define DCHECK(x) require(x)
#else
#define DCHECK(x) ((void)0)
#endif
struct Isolate {};
template<class T> using Tagged = T*;
template<class T> struct Handle {
 T* value;
 Handle(T* p, Isolate*) : value(p) {}
 operator T*() const {return value;}
};
inline unsigned no_gc_depth=0;
struct DisallowGarbageCollection {DisallowGarbageCollection() {++no_gc_depth;} ~DisallowGarbageCollection() {--no_gc_depth;}};
struct BytecodeOffset {int value; bool IsNone() const {return value<0;} int ToInt() const {return value;}};
struct Code {int id; bool optimized;};
namespace interpreter {enum class Bytecode {kOther, kJumpLoop};}
struct Instruction {interpreter::Bytecode opcode=interpreter::Bytecode::kOther; int target=-1; int level=-1; int slot=-1;};
struct BytecodeArray {std::vector<Instruction> values;};
struct FeedbackVector {
 std::vector<Code> codes;
 bool maybe_has_optimized_osr_code() const {return std::any_of(codes.begin(), codes.end(), [](const Code& c) {return c.optimized;});}
 std::optional<Tagged<Code>> GetOptimizedOsrCode(Isolate*, int slot) {
  require(slot>=0 && static_cast<size_t>(slot)<codes.size());
  if (codes[slot].optimized) {return &codes[slot];}
  return std::nullopt;
 }
};
struct Shared {BytecodeArray* code; BytecodeArray* GetBytecodeArray(Isolate*) {return code;}};
struct JSFunction {
 FeedbackVector feedback; Shared info; std::vector<int> deoptimized;
 FeedbackVector* feedback_vector() {return &feedback;}
 Shared* shared() {return &info;}
};
namespace interpreter {
class BytecodeArrayIterator {
 BytecodeArray* array_; int offset_;
public:
 BytecodeArrayIterator(BytecodeArray* array, int offset);
 static bool IsValidOffset(BytecodeArray* array,int offset);
 bool done() const;
 void Advance();
 void SetOffset(int offset);
 int current_offset() const;
 Bytecode current_bytecode() const;
 int GetJumpTargetOffset() const;
 int GetImmediateOperand(int operand) const;
 int GetSlotOperand(int operand) const;
};
}
namespace base {
template<class T, size_t N> using SmallVector = std::vector<T>;
inline bool IsInRange(int value,int low,int high) {return low<=value && value<=high;}
}
struct Flags {bool use_ic=true;};
extern Flags v8_flags;
enum class LazyDeoptimizeReason {kEagerDeopt};
struct Deoptimizer {
 static void DeoptimizeFunction(JSFunction* function, LazyDeoptimizeReason reason, Code* code) {
  require(reason==LazyDeoptimizeReason::kEagerDeopt && code->optimized);
  code->optimized=false; function->deoptimized.push_back(code->id);
 }
};
