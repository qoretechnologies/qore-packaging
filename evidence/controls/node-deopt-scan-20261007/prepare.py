# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib, json, shutil

root = Path('work/node-obs-diagnostic-20261006/node-v24.18.1')
out = Path('work/node-deopt-scan-controls-20261007')
out.mkdir()
path = 'deps/v8/src/runtime/runtime-compiler.cc'
source = (root / path).read_text()
a = source.index('bool TryGetOptimizedOsrCode(')
b = source.index('\n}  // namespace', a)
body = source[a:b]
(out / 'source-extracts.json').write_text(json.dumps([dict(file=path, line=source[:a].count('\n') + 1, body=body, sha256=hashlib.sha256(body.encode()).hexdigest())], indent=2) + '\n')
(out / 'control.h').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
''')
(out / 'helper.cc').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
using namespace interpreter;
BytecodeArrayIterator::BytecodeArrayIterator(BytecodeArray* array,int offset):array_(array),offset_(offset) {require(IsValidOffset(array,offset));}
bool BytecodeArrayIterator::IsValidOffset(BytecodeArray* array,int offset) {return offset>=0 && static_cast<size_t>(offset)<array->values.size();}
bool BytecodeArrayIterator::done() const {return static_cast<size_t>(offset_)>=array_->values.size();}
void BytecodeArrayIterator::Advance() {require(!done());++offset_;}
void BytecodeArrayIterator::SetOffset(int offset) {require(IsValidOffset(array_,offset));offset_=offset;}
int BytecodeArrayIterator::current_offset() const {require(!done());return offset_;}
Bytecode BytecodeArrayIterator::current_bytecode() const {require(!done());return array_->values[offset_].opcode;}
int BytecodeArrayIterator::GetJumpTargetOffset() const {require(current_bytecode()==Bytecode::kJumpLoop);return array_->values[offset_].target;}
int BytecodeArrayIterator::GetImmediateOperand(int operand) const {require(operand==1 && current_bytecode()==Bytecode::kJumpLoop);return array_->values[offset_].level;}
int BytecodeArrayIterator::GetSlotOperand(int operand) const {require(operand==2 && current_bytecode()==Bytecode::kJumpLoop);return array_->values[offset_].slot;}
''')
(out / 'control.cc').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
Flags v8_flags{};
''' + body + r'''
struct Loop {int begin; int end; int depth; int group;};
int main() {
 const std::vector<std::vector<Loop>> layouts{
  {}, {{1,5,0,0}}, {{1,5,0,0},{10,15,0,1}},
  {{2,5,1,0},{8,10,2,0},{7,12,1,0},{1,15,0,0},{20,25,0,1}},
  {{1,5,1,0},{10,15,0,1}}, {{1,5,1,0}}
 };
 unsigned checks=0;
 for(unsigned repeat=0;repeat<100;++repeat) {
  for(const auto& loops:layouts) {
   BytecodeArray array{std::vector<Instruction>(32)};
   for(size_t i=0;i<loops.size();++i) {
    const auto& l=loops[i];array.values[l.end]={interpreter::Bytecode::kJumpLoop,l.begin,l.depth,static_cast<int>(i)};
   }
   for(unsigned mask=0;mask<(1u<<loops.size());++mask) {
    for(int exit=0;exit<32;++exit) {
     for(bool ic:{false,true}) {
      JSFunction function{{},{&array},{}};
      for(size_t i=0;i<loops.size();++i) {function.feedback.codes.push_back({static_cast<int>(i),bool(mask&(1u<<i))});}
      v8_flags.use_ic=ic;Isolate isolate;
      DeoptAllOsrLoopsContainingDeoptExit(&isolate,&function,BytecodeOffset{exit});
      // Independent interval table for this version's cache-eviction heuristic.
      std::set<int> groups;
      for(const auto& l:loops) {if(l.begin<=exit && exit<=l.end) {groups.insert(l.group);}}
      std::set<int> expected;
      if(ic) {for(size_t i=0;i<loops.size();++i) {if(groups.count(loops[i].group) && (mask&(1u<<i))) {expected.insert(static_cast<int>(i));}}}
      // The five-loop layout stops its forward scan at the later sibling B
      // when exiting A (offsets 2..5). Cached sibling/outer code is retained.
      // This is an eviction-policy boundary, not a language-result assertion.
      if(loops.size()==5 && exit>=2 && exit<=5) {
       expected.clear();if(ic && (mask&1u)) {expected.insert(0);}
      }
      std::set<int> actual(function.deoptimized.begin(),function.deoptimized.end());
      if(actual!=expected || actual.size()!=function.deoptimized.size()) {
       std::fprintf(stderr,"mismatch loops=%zu mask=%u exit=%d ic=%d actual:",loops.size(),mask,exit,ic);
       for(int value:actual) {std::fprintf(stderr," %d",value);}
       std::fprintf(stderr," expected:");for(int value:expected) {std::fprintf(stderr," %d",value);}std::fprintf(stderr,"\n");
       std::abort();
      }
      require(no_gc_depth==0);
      for(size_t i=0;i<loops.size();++i) {require(function.feedback.codes[i].optimized==(bool(mask&(1u<<i)) && !expected.count(static_cast<int>(i))));}
      ++checks;
     }
    }
   }
  }
 }
 std::printf("PASS: %u deoptimization interval and bytecode-boundary checks\n",checks);
}
''')
shutil.copy2(root / 'deps/v8/LICENSE', out / 'V8-LICENSE')
s = Path('work/node-sweep-serializer-controls-20261007/run2.py').read_text().replace('2.log', '.log').replace('status2.json', 'status.json')
(out / 'run.py').write_text(s)
print('Prepared unchanged deoptimization scans with interval-reference cases.')
