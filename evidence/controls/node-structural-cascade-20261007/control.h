// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <type_traits>
#include <vector>
inline void require(bool c) {if(!c) {std::abort();}}
#define TRACE(...) ((void)0)
#define CHECK_EQ(a,b) require((a)==(b))
#ifdef DEBUG
#define DCHECK(x) require(bool(x))
#define DCHECK_NE(a,b) require((a)!=(b))
#else
#define DCHECK(x) ((void)0)
#define DCHECK_NE(a,b) ((void)0)
#endif
#define LABEL_BLOCK(label) for (;false;std::abort()) label:
struct OpIndex {
  int value;
  static OpIndex Invalid() {return {-1};}
  bool valid() const {return value>=0;}
  bool operator==(const OpIndex&) const=default;
};
enum class BranchHint {kNone,kTrue,kFalse};
struct ComparisonOp;struct ConstantOp;struct BranchOp;struct Block;struct Graph;
namespace Opmask {struct kWord32Equal {};struct kWord32Constant {};}
struct Operation {
  enum class Kind {Var,Equal,OtherComparison,Constant,OtherConstant,Branch,End};
  const Kind kind;
  explicit Operation(Kind k):kind(k) {}
  virtual ~Operation()=default;
  template<class T> bool Is() const;
  template<class T> const T& Cast() const {require(Is<T>());return static_cast<const T&>(*this);}
  template<class T> const ComparisonOp* TryCast() const;
};
struct ComparisonOp:Operation {
  OpIndex lhs,rhs;
  ComparisonOp(OpIndex left,OpIndex right,bool eq=true):Operation(eq?Kind::Equal:Kind::OtherComparison),lhs(left),rhs(right) {}
  OpIndex left() const {return lhs;} OpIndex right() const {return rhs;}
};
struct ConstantOp:Operation {
  uint32_t value;
  ConstantOp(uint32_t v,bool word=true):Operation(word?Kind::Constant:Kind::OtherConstant),value(v) {}
  uint32_t word32() const {return value;}
};
struct BranchOp:Operation {
  OpIndex cond;Block* if_true;Block* if_false;BranchHint hint;
  BranchOp(OpIndex c,Block* t,Block* f,BranchHint h):Operation(Kind::Branch),cond(c),if_true(t),if_false(f),hint(h) {}
  OpIndex condition() const {return cond;}
};
template<class T> bool Operation::Is() const {
  if constexpr(std::is_same_v<T,ComparisonOp>) {return kind==Kind::Equal||kind==Kind::OtherComparison;}
  else if constexpr(std::is_same_v<T,ConstantOp>||std::is_same_v<T,Opmask::kWord32Constant>) {return kind==Kind::Constant;}
  else if constexpr(std::is_same_v<T,BranchOp>) {return kind==Kind::Branch;}
  else {std::abort();}
}
template<class T> const ComparisonOp* Operation::TryCast() const {
  static_assert(std::is_same_v<T,Opmask::kWord32Equal>);
  return kind==Kind::Equal?static_cast<const ComparisonOp*>(this):nullptr;
}
struct Block {
  unsigned id;
  bool pure=true;
  OpIndex last=OpIndex::Invalid();
  const Operation& LastOperation(const Graph&) const;
};
struct Graph {
  std::vector<std::unique_ptr<Operation>> operations;
  std::vector<std::unique_ptr<Block>> blocks;
  template<class T,class... A> OpIndex add(A&&... args) {
    operations.push_back(std::make_unique<T>(std::forward<A>(args)...));return {static_cast<int>(operations.size()-1)};
  }
  Block* block() {auto b=std::make_unique<Block>();b->id=blocks.size();auto* p=b.get();blocks.push_back(std::move(b));return p;}
  const Operation& Get(OpIndex index) const {require(index.valid()&&size_t(index.value)<operations.size());return *operations[index.value];}
};
struct SwitchOp {struct Case {uint32_t value;Block* destination;BranchHint hint;Case(uint32_t v,Block* d,BranchHint h):value(v),destination(d),hint(h) {}};};
namespace base {template<class T,unsigned N> using SmallVector=std::vector<T>;}
struct NextReducer {static OpIndex ReduceInputGraphBranch(OpIndex,const BranchOp&) {return {0};}};
template<class Next> struct StructuralOptimizationReducer:Next {
  Graph graph;bool skip=false;
  std::vector<SwitchOp::Case> emitted;
  std::vector<const Block*> inlined;
  Block* default_block=nullptr;BranchHint default_hint=BranchHint::kNone;OpIndex switched=OpIndex::Invalid();
  bool ShouldSkipOptimizationStep() const {return skip;}
  auto& Asm() {return *this;}
  Graph& input_graph() {return graph;}
  Block* MapToNewGraph(Block* b) {return b;}
  static bool ContainsOnlyPureOps(const Block* block,const Graph&) {return block->pure;}
  OpIndex EmitSwitch(OpIndex variable,base::SmallVector<SwitchOp::Case,16>& cases,base::SmallVector<const Block*,16>& false_blocks,Block* last,BranchHint hint) {
    require(last && false_blocks.back()==last);switched=variable;emitted=cases;inlined=false_blocks;default_block=last;default_hint=hint;return {99};
  }
  OpIndex ReduceInputGraphBranch(OpIndex input_index, const BranchOp& branch) {
    LABEL_BLOCK(no_change) {
      return Next::ReduceInputGraphBranch(input_index, branch);
    }
    if (ShouldSkipOptimizationStep()) goto no_change;

    TRACE("[structural] Calling ReduceInputGraphBranch for index: %u\n",
          static_cast<unsigned int>(input_index.id()));

    base::SmallVector<SwitchOp::Case, 16> cases;
    base::SmallVector<const Block*, 16> false_blocks;

    Block* current_if_true;
    Block* current_if_false;
    const BranchOp* current_branch = &branch;
    BranchHint current_branch_hint;
    BranchHint next_hint = BranchHint::kNone;

    OpIndex switch_var = OpIndex::Invalid();
    uint32_t value;
    while (true) {
      // If we encounter a condition that is not equality, we can't turn it
      // into a switch case.
      const Operation& cond =
          Asm().input_graph().Get(current_branch->condition());

      if (!cond.template Is<ComparisonOp>()) {
        // 'if(x==0)' may be optimized to 'if(x)', we should take this into
        // consideration.

        // The "false" destination will be inlined before the switch is emitted,
        // so it should only contain pure operations.
        if (!ContainsOnlyPureOps(current_branch->if_true,
                                 Asm().input_graph())) {
          TRACE("\t [break] End of only-pure-ops cascade reached.\n");
          break;
        }

        OpIndex current_var = current_branch->condition();
        if (!switch_var.valid()) {
          switch_var = current_var;
        } else if (switch_var != current_var) {
          TRACE("\t [bailout] Not all branches compare the same variable.\n");
          break;
        }
        value = 0;
        // The true/false of 'if(x)' is reversed from 'if(x==0)'
        current_if_true = current_branch->if_false;
        current_if_false = current_branch->if_true;
        const BranchHint hint = current_branch->hint;
        current_branch_hint = hint == BranchHint::kNone   ? BranchHint::kNone
                              : hint == BranchHint::kTrue ? BranchHint::kFalse
                                                          : BranchHint::kTrue;
      } else {
        const ComparisonOp* equal =
            cond.template TryCast<Opmask::kWord32Equal>();
        if (!equal) {
          TRACE(
              "\t [bailout] Branch with different condition than Word32 "
              "Equal.\n");
          break;
        }
        // MachineOptimizationReducer should normalize equality to put constants
        // right.
        const Operation& right_op = Asm().input_graph().Get(equal->right());
        if (!right_op.Is<Opmask::kWord32Constant>()) {
          TRACE(
              "\t [bailout] No Word32 constant on the right side of Equal.\n");
          break;
        }

        // The "false" destination will be inlined before the switch is emitted,
        // so it should only contain pure operations.
        if (!ContainsOnlyPureOps(current_branch->if_false,
                                 Asm().input_graph())) {
          TRACE("\t [break] End of only-pure-ops cascade reached.\n");
          break;
        }
        const ConstantOp& const_op = right_op.Cast<ConstantOp>();
        value = const_op.word32();

        // If we encounter equal to a different value, we can't introduce
        // a switch.
        OpIndex current_var = equal->left();
        if (!switch_var.valid()) {
          switch_var = current_var;
        } else if (switch_var != current_var) {
          TRACE("\t [bailout] Not all branches compare the same variable.\n");
          break;
        }

        current_if_true = current_branch->if_true;
        current_if_false = current_branch->if_false;
        current_branch_hint = current_branch->hint;
      }

      DCHECK(current_if_true && current_if_false);

      // We can't just use `current_branch->hint` for every case. Consider:
      //
      //     if (a) { }
      //     else if (b) { }
      //     else if (likely(c)) { }
      //     else if (d) { }
      //     else { }
      //
      // The fact that `c` is Likely doesn't tell anything about the likelyness
      // of `a` and `b` compared to `c`, which means that `c` shouldn't have the
      // Likely hint in the switch. However, since `c` is likely here, it means
      // that `d` and "default" are both unlikely, even in the switch.
      //
      // So, for the 1st case, we use `current_branch->hint`.
      // Then, when we encounter a Likely hint, we mark all of the subsequent
      // cases are Unlikely, but don't mark the current one as Likely. This is
      // done with the `next_hint` variable, which is initially kNone, but
      // because kFalse when we encounter a Likely branch.
      // We never set `next_hint` as kTrue as it would only apply to subsequent
      // cases and not to already-emitted cases. The only case that could thus
      // have a kTrue annotation is the 1st one.
      DCHECK_NE(next_hint, BranchHint::kTrue);
      BranchHint hint = next_hint;
      if (cases.size() == 0) {
        // The 1st case gets its original hint.
        hint = current_branch_hint;
      } else if (current_branch_hint == BranchHint::kFalse) {
        // For other cases, if the branch has a kFalse hint, we do use it,
        // regardless of `next_hint`.
        hint = BranchHint::kNone;
      }
      if (current_branch_hint == BranchHint::kTrue) {
        // This branch is likely true, which means that all subsequent cases are
        // unlikely.
        next_hint = BranchHint::kFalse;
      }

      // The current_if_true block becomes the corresponding switch case block.
      cases.emplace_back(value, Asm().MapToNewGraph(current_if_true), hint);

      // All pure ops from the if_false block should be executed before
      // the switch, except the last Branch operation (which we drop).
      false_blocks.push_back(current_if_false);

      // If we encounter a if_false block that doesn't end with a Branch,
      // this means we've reached the end of the cascade.
      const Operation& maybe_branch =
          current_if_false->LastOperation(Asm().input_graph());
      if (!maybe_branch.Is<BranchOp>()) {
        TRACE("\t [break] Reached end of the if-else cascade.\n");
        break;
      }

      // Iterate to the next if_false block in the cascade.
      current_branch = &maybe_branch.template Cast<BranchOp>();
    }

    // Probably better to keep short if-else cascades as they are.
    if (cases.size() <= 2) {
      TRACE("\t [bailout] Cascade with less than 2 levels of nesting.\n");
      goto no_change;
    }
    CHECK_EQ(cases.size(), false_blocks.size());

    // Sorting the cases because it will help figure out if there is a duplicate
    // case (in which case we bailout, since this is not well handled by the
    // code generator).
    // Note that this isn't wasted work: there is a good chance that the
    // instruction selector will emit a binary search for this switch, which
    // will require the cases to be sorted.
    std::stable_sort(
        cases.begin(), cases.end(),
        [](SwitchOp::Case a, SwitchOp::Case b) { return a.value < b.value; });
    auto it = std::adjacent_find(
        cases.begin(), cases.end(),
        [](SwitchOp::Case a, SwitchOp::Case b) { return a.value == b.value; });
    if (it != cases.end()) {
      TRACE("\t [bailout] Multiple cases with the value %d.\n", (*it).value);
      goto no_change;
    }

    TRACE("[reduce] Successfully emit a Switch with %zu cases.\n",
          cases.size());
    return EmitSwitch(switch_var, cases, false_blocks, current_if_false,
                      next_hint);
  }

};
