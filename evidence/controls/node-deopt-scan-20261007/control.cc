// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
Flags v8_flags{};
bool TryGetOptimizedOsrCode(Isolate* isolate, Tagged<FeedbackVector> vector,
                            const interpreter::BytecodeArrayIterator& it,
                            Tagged<Code>* code_out) {
  std::optional<Tagged<Code>> maybe_code =
      vector->GetOptimizedOsrCode(isolate, it.GetSlotOperand(2));
  if (maybe_code.has_value()) {
    *code_out = maybe_code.value();
    return true;
  }
  return false;
}

// Deoptimize all osr'd loops which is in the same outermost loop with deopt
// exit. For example:
//  for (;;) {
//    for (;;) {
//    }  // Type a: loop start < OSR backedge < deopt exit
//    for (;;) {
//      <- Deopt
//      for (;;) {
//      }  // Type b: deopt exit < loop start < OSR backedge
//    } // Type c: loop start < deopt exit < OSR backedge
//  }  // The outermost loop
void DeoptAllOsrLoopsContainingDeoptExit(Isolate* isolate,
                                         Tagged<JSFunction> function,
                                         BytecodeOffset deopt_exit_offset) {
  DisallowGarbageCollection no_gc;
  DCHECK(!deopt_exit_offset.IsNone());

  if (!v8_flags.use_ic ||
      !function->feedback_vector()->maybe_has_optimized_osr_code()) {
    return;
  }
  Handle<BytecodeArray> bytecode_array(
      function->shared()->GetBytecodeArray(isolate), isolate);
  DCHECK(interpreter::BytecodeArrayIterator::IsValidOffset(
      bytecode_array, deopt_exit_offset.ToInt()));

  interpreter::BytecodeArrayIterator it(bytecode_array,
                                        deopt_exit_offset.ToInt());

  Tagged<FeedbackVector> vector = function->feedback_vector();
  Tagged<Code> code;
  base::SmallVector<Tagged<Code>, 8> osr_codes;
  // Visit before the first loop-with-deopt is found
  for (; !it.done(); it.Advance()) {
    // We're only interested in loop ranges.
    if (it.current_bytecode() != interpreter::Bytecode::kJumpLoop) continue;
    // Is the deopt exit contained in the current loop?
    if (base::IsInRange(deopt_exit_offset.ToInt(), it.GetJumpTargetOffset(),
                        it.current_offset())) {
      break;
    }
    // We've reached nesting level 0, i.e. the current JumpLoop concludes a
    // top-level loop, return as the deopt exit is not in any loop. For example:
    //  <- Deopt
    //  for (;;) {
    //  } // The outermost loop
    const int loop_nesting_level = it.GetImmediateOperand(1);
    if (loop_nesting_level == 0) return;
    if (TryGetOptimizedOsrCode(isolate, vector, it, &code)) {
      // Collect type b osr'd loops
      osr_codes.push_back(code);
    }
  }
  if (it.done()) return;
  for (size_t i = 0, size = osr_codes.size(); i < size; i++) {
    // Deoptimize type b osr'd loops
    Deoptimizer::DeoptimizeFunction(function, LazyDeoptimizeReason::kEagerDeopt,
                                    osr_codes[i]);
  }
  // Visit after the first loop-with-deopt is found
  int last_deopt_in_range_loop_jump_target;
  for (; !it.done(); it.Advance()) {
    // We're only interested in loop ranges.
    if (it.current_bytecode() != interpreter::Bytecode::kJumpLoop) continue;
    // We've reached a new nesting loop in the case of the deopt exit is in a
    // loop whose outermost loop was removed. For example:
    //  for (;;) {
    //    <- Deopt
    //  } // The non-outermost loop
    //  for (;;) {
    //  } // The outermost loop
    if (it.GetJumpTargetOffset() > deopt_exit_offset.ToInt()) break;
    last_deopt_in_range_loop_jump_target = it.GetJumpTargetOffset();
    if (TryGetOptimizedOsrCode(isolate, vector, it, &code)) {
      // Deoptimize type c osr'd loops
      Deoptimizer::DeoptimizeFunction(function,
                                      LazyDeoptimizeReason::kEagerDeopt, code);
    }
    // We've reached nesting level 0, i.e. the current JumpLoop concludes a
    // top-level loop.
    const int loop_nesting_level = it.GetImmediateOperand(1);
    if (loop_nesting_level == 0) break;
  }
  if (it.done()) return;
  // Revisit from start of the last deopt in range loop to deopt
  for (it.SetOffset(last_deopt_in_range_loop_jump_target);
       it.current_offset() < deopt_exit_offset.ToInt(); it.Advance()) {
    // We're only interested in loop ranges.
    if (it.current_bytecode() != interpreter::Bytecode::kJumpLoop) continue;
    if (TryGetOptimizedOsrCode(isolate, vector, it, &code)) {
      // Deoptimize type a osr'd loops
      Deoptimizer::DeoptimizeFunction(function,
                                      LazyDeoptimizeReason::kEagerDeopt, code);
    }
  }
}

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
