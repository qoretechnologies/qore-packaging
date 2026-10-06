// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// The marked method bodies are copied unchanged from V8; see V8-LICENSE.
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <type_traits>
#include <vector>
#define REQUIRE(x) do { if (!(x)) { std::fprintf(stderr, "%d: %s\n", __LINE__, #x); std::abort(); } } while (false)
static unsigned checks=0;

struct Block { unsigned id=0; };
using block_t=Block;
using ConditionWithHint=bool;
struct Flow {
 std::array<Block,32> blocks{};
 unsigned created=0, bound=0, gotos=0, branches=0;
 unsigned mask;
 Block* current=nullptr;
 explicit Flow(unsigned m):mask(m) {}
 Flow& Asm() { return *this; }
 Block* NewBlock() { REQUIRE(created<blocks.size()); blocks[created].id=created; return &blocks[created++]; }
 void validate(Block* p) { REQUIRE(p>=blocks.data() && p<blocks.data()+created); REQUIRE(&blocks[p->id]==p); ++checks; }
 void Branch(bool, Block* a, Block* b) { validate(a);validate(b);++branches;current=nullptr; }
 bool Bind(Block* p) { validate(p); ++bound; if ((mask>>(p->id%8))&1) { current=p;return true; } current=nullptr;return false; }
 Block* current_block() { return current; }
 void Goto(Block* p) { validate(p);REQUIRE(current);current=nullptr;++gotos; }
// BEGIN unchanged V8 flow-state methods
  struct ControlFlowHelper_IfState {
    block_t* else_block;
    block_t* end_block;
  };

  bool ControlFlowHelper_BindIf(ConditionWithHint condition,
                                ControlFlowHelper_IfState* state) {
    block_t* then_block = Asm().NewBlock();
    state->else_block = Asm().NewBlock();
    state->end_block = Asm().NewBlock();
    Asm().Branch(condition, then_block, state->else_block);
    return Asm().Bind(then_block);
  }

  bool ControlFlowHelper_BindIfNot(ConditionWithHint condition,
                                   ControlFlowHelper_IfState* state) {
    block_t* then_block = Asm().NewBlock();
    state->else_block = Asm().NewBlock();
    state->end_block = Asm().NewBlock();
    Asm().Branch(condition, state->else_block, then_block);
    return Asm().Bind(then_block);
  }

  bool ControlFlowHelper_BindElse(ControlFlowHelper_IfState* state) {
    block_t* else_block = state->else_block;
    state->else_block = nullptr;
    return Asm().Bind(else_block);
  }

  void ControlFlowHelper_FinishIfBlock(ControlFlowHelper_IfState* state) {
    if (Asm().current_block() == nullptr) return;
    Asm().Goto(state->end_block);
  }

  void ControlFlowHelper_EndIf(ControlFlowHelper_IfState* state) {
    if (state->else_block) {
      if (Asm().Bind(state->else_block)) {
        Asm().Goto(state->end_block);
      }
    }
    Asm().Bind(state->end_block);
  }
// END unchanged V8 flow-state methods
 void run(bool invert, bool nested, bool with_else);
};
#include "src/compiler/turboshaft/define-assembler-macros.inc"
void Flow::run(bool invert, bool nested, bool with_else) {
 if (invert) {
  IF_NOT(true) { REQUIRE(current && current->id==0);++checks; }
  ELSE { REQUIRE(current && current->id==1);++checks; }
 } else if (with_else) {
  IF(true) {
   REQUIRE(current && current->id==0);++checks;
   if (nested) {
    IF(false) { REQUIRE(current && current->id==3);++checks; }
    ELSE { REQUIRE(current && current->id==4);++checks; }
   }
  } ELSE { REQUIRE(current && current->id==1);++checks; }
 } else {
  IF(true) { REQUIRE(current && current->id==0);++checks; }
 }
 REQUIRE(created == (nested && !invert && with_else && (mask&1) ? 6u : 3u));
 REQUIRE(branches == created/3); REQUIRE(bound >= 3); ++checks;
}
#include "src/compiler/turboshaft/undef-assembler-macros.inc"
struct PhiOp {};
struct Operation {
 unsigned key;
 size_t hash;
 template<class T> bool Is() const { return std::is_same_v<T,Operation>; }
 template<class T> const T& Cast() const { static_assert(std::is_same_v<T,Operation>);return *this; }
 bool EqualsForGVN(const Operation& other) const { return key==other.key; }
};
struct HashControl {
 struct Entry {
  size_t value=0;
  unsigned block=0;
  size_t hash=0;
  bool IsEmpty() const { return hash==0; }
 };
 std::array<Entry,128> table_{};
 std::vector<Operation> operations;
 size_t mask_=127;
 HashControl& Asm() { return *this; }
 HashControl& output_graph() { return *this; }
 HashControl* current_block() { return this; }
 unsigned index() const { return 0; }
 const Operation& Get(size_t value) const { REQUIRE(value<operations.size());return operations[value]; }
 size_t NextEntryIndex(size_t i) const { return (i+1)&mask_; }
 template<bool same_block_only, class Op> size_t ComputeHash(const Op& op) {
  static_assert(!same_block_only); return op.hash ? op.hash : 1;
 }
#define DCHECK_NE(a,b) REQUIRE((a)!=(b))
// BEGIN unchanged V8 Find method
  template <class Op>
  Entry* Find(const Op& op, size_t* hash_ret = nullptr) {
    constexpr bool same_block_only = std::is_same<Op, PhiOp>::value;
    size_t hash = ComputeHash<same_block_only>(op);
    size_t start_index = hash & mask_;
    for (size_t i = start_index;; i = NextEntryIndex(i)) {
      Entry& entry = table_[i];
      if (entry.IsEmpty()) {
        // We didn't find {op} in {table_}. Returning where it could be
        // inserted.
        if (hash_ret) *hash_ret = hash;
        return &entry;
      }
      if (entry.hash == hash) {
        const Operation& entry_op = Asm().output_graph().Get(entry.value);
        if (entry_op.Is<Op>() &&
            (!same_block_only ||
             entry.block == Asm().current_block()->index()) &&
            entry_op.Cast<Op>().EqualsForGVN(op)) {
          return &entry;
        }
      }
      // Making sure that we don't have an infinite loop.
      DCHECK_NE(start_index, NextEntryIndex(i));
    }
  }

// END unchanged V8 Find method
#undef DCHECK_NE
 void check(unsigned key,size_t hash,bool expected_hit) {
  Operation op{key,hash};size_t computed=0xabcdef;
  Entry* entry=Find(op,&computed);
  if (entry->IsEmpty()) {
   REQUIRE(!expected_hit); REQUIRE(computed==(hash?hash:1));
   *entry=Entry{operations.size(),0,computed};operations.push_back(op);
  } else {
   REQUIRE(expected_hit);REQUIRE(computed==0xabcdef);REQUIRE(Get(entry->value).key==key);
  }
  REQUIRE(Find(op)==entry);++checks;
 }
};
int main() {
 for(unsigned repeat=0;repeat<1000;++repeat) {
  for(unsigned mask=0;mask<256;++mask) {
   for(unsigned mode=0;mode<8;++mode) {
    Flow f(mask);f.run(mode&1,mode&2,mode&4);
   }
  }
  for(unsigned mode=0;mode<4;++mode) {
   HashControl h;
   for(unsigned key=0;key<64;++key) {
    size_t hash=mode==0?0:mode==1?127:mode==2?key*128u:~size_t(key);
    h.check(key,hash,false);h.check(key,hash,true);
   }
   for(unsigned key=64;key>0;--key) {
    unsigned k=key-1;size_t hash=mode==0?0:mode==1?127:mode==2?k*128u:~size_t(k);
    h.check(k,hash,true);
   }
  }
 }
 std::printf("%u graph-state and guarded-hash checks passed\n",checks);
}
