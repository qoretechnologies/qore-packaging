// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <numeric>
#include <optional>
#include <vector>
void require(bool value) {if(!value) {std::abort();}}
#ifdef DEBUG
#define DCHECK(x) require(x)
#else
#define DCHECK(x) ((void)0)
#endif
struct RegExpLookaround {enum class Type {LOOKBEHIND, LOOKAHEAD};};
struct LookaroundPayload {
 int id=0; RegExpLookaround::Type kind=RegExpLookaround::Type::LOOKBEHIND;
 int index() const {return id;}
 RegExpLookaround::Type type() const {return kind;}
};
struct RegExpInstruction {
  enum Opcode : int32_t {
    ACCEPT,
    ASSERTION,
    CLEAR_REGISTER,
    CONSUME_RANGE,
    RANGE_COUNT,
    FORK,
    JMP,
    SET_REGISTER_TO_CP,
    SET_QUANTIFIER_TO_CLOCK,
    FILTER_QUANTIFIER,
    FILTER_GROUP,
    FILTER_LOOKAROUND,
    FILTER_CHILD,
    BEGIN_LOOP,
    END_LOOP,
    START_LOOKAROUND,
    END_LOOKAROUND,
    WRITE_LOOKAROUND_TABLE,
    READ_LOOKAROUND_TABLE,
  };
 Opcode opcode=ACCEPT;
 struct Payload {LookaroundPayload lookaround; int quantifier_id=0;} payload;
  static bool IsFilter(const RegExpInstruction& instruction) {
    return instruction.opcode == RegExpInstruction::Opcode::FILTER_GROUP ||
           instruction.opcode == RegExpInstruction::Opcode::FILTER_QUANTIFIER ||
           instruction.opcode == RegExpInstruction::Opcode::FILTER_CHILD;
  }
};
template<class T> struct ZoneList {
 std::vector<T> values;
 int length() const {return static_cast<int>(values.size());}
 T& operator[](int i) {require(i>=0 && i<length());return values[i];}
 void Add(T value,int) {values.push_back(value);}
 void Set(int i,T value) {require(i>=0 && i<length());values[i]=value;}
};
struct Lookaround {int match_pc; int capture_pc; RegExpLookaround::Type type;};
struct Flags {bool experimental_regexp_engine_capture_group_opt=true;} v8_flags;
struct Interpreter {
 ZoneList<RegExpInstruction> bytecode_;
 ZoneList<Lookaround> lookarounds_;
 bool only_captureless_lookbehinds_=true;
 std::optional<int> filter_groups_pc_;
 int quantifier_count_=0;
 int zone_=0;
 void Scan();
};
__attribute__((noinline)) void Interpreter::Scan() {
    std::optional<struct Lookaround> lookaround;
    bool in_lookaround = false;
    int lookaround_index;
    for (int i = 0; i < bytecode_.length() - 1; ++i) {
      auto& inst = bytecode_[i];

      if (inst.opcode == RegExpInstruction::START_LOOKAROUND) {
        DCHECK(!lookaround.has_value());
        in_lookaround = true;

        // Stores the partial information for a lookaround. The rest will be
        // determined upon reaching a `WRITE_LOOKAROUND_TABLE` instruction.
        lookaround_index = inst.payload.lookaround.index();
        lookaround = Lookaround{.match_pc = i,
                                .capture_pc = -1,
                                .type = inst.payload.lookaround.type()};

        if (inst.payload.lookaround.type() ==
            RegExpLookaround::Type::LOOKAHEAD) {
          only_captureless_lookbehinds_ = false;
        }
      }

      if (inst.opcode == RegExpInstruction::SET_REGISTER_TO_CP &&
          in_lookaround) {
        only_captureless_lookbehinds_ = false;
      }

      if (inst.opcode == RegExpInstruction::WRITE_LOOKAROUND_TABLE) {
        DCHECK(lookaround.has_value());

        // Fills the current lookaround data.
        lookaround->capture_pc = i + 1;

        // Since the lookarounds are not in order in the `lookarounds_` array,
        // we first fill it until it has the correct size.
        while (lookarounds_.length() <= lookaround_index) {
          lookarounds_.Add({-1, -1, RegExpLookaround::Type::LOOKBEHIND}, zone_);
        }
        lookarounds_.Set(lookaround_index, *lookaround);
        lookaround = {};
      }

      if (inst.opcode == RegExpInstruction::END_LOOKAROUND) {
        in_lookaround = false;
      }

      // The first `FILTER_*` instruction encountered is the start of the
      // `FILTER_*` section.
      if (!filter_groups_pc_.has_value() && RegExpInstruction::IsFilter(inst)) {
        DCHECK(v8_flags.experimental_regexp_engine_capture_group_opt);
        filter_groups_pc_ = i;
      }

      if (inst.opcode == RegExpInstruction::SET_QUANTIFIER_TO_CLOCK) {
        DCHECK(v8_flags.experimental_regexp_engine_capture_group_opt);
        quantifier_count_ =
            std::max(quantifier_count_, inst.payload.quantifier_id + 1);
      }
    }
}
int main() {
 unsigned checks=0;
 for(unsigned repeat=0;repeat<10;++repeat) {
  for(unsigned count=0;count<=4;++count) {
   std::vector<int> order(count);std::iota(order.begin(),order.end(),0);
   do {
    for(unsigned types=0;types<(1u<<count);++types) {
     for(unsigned captures=0;captures<(1u<<count);++captures) {
      for(bool gaps:{false,true}) {
       Interpreter scan;
       std::vector<Lookaround> expected(count*(gaps?2:1),{-1,-1,RegExpLookaround::Type::LOOKBEHIND});
       auto emit=[&](RegExpInstruction::Opcode opcode) {RegExpInstruction inst;inst.opcode=opcode;scan.bytecode_.values.push_back(inst);};
       bool simple=true;
       emit(RegExpInstruction::SET_REGISTER_TO_CP); // outside a lookaround
       for(int raw:order) {
        int index=gaps?raw*2+1:raw;
        auto type=(types&(1u<<raw))?RegExpLookaround::Type::LOOKAHEAD:RegExpLookaround::Type::LOOKBEHIND;
        int match=scan.bytecode_.length();emit(RegExpInstruction::START_LOOKAROUND);
        scan.bytecode_.values.back().payload.lookaround={index,type};
        emit(RegExpInstruction::CONSUME_RANGE);
        if(captures&(1u<<raw)) {emit(RegExpInstruction::SET_REGISTER_TO_CP);simple=false;}
        if(type==RegExpLookaround::Type::LOOKAHEAD) {simple=false;}
        emit(RegExpInstruction::WRITE_LOOKAROUND_TABLE);
        expected[index]={match,scan.bytecode_.length(),type};
        emit(RegExpInstruction::CONSUME_RANGE);emit(RegExpInstruction::END_LOOKAROUND);
       }
       emit(RegExpInstruction::SET_REGISTER_TO_CP);
       for(int id:{0,5,2,5}) {emit(RegExpInstruction::SET_QUANTIFIER_TO_CLOCK);scan.bytecode_.values.back().payload.quantifier_id=id;}
       int filter=scan.bytecode_.length();emit(RegExpInstruction::FILTER_GROUP);emit(RegExpInstruction::FILTER_CHILD);emit(RegExpInstruction::ACCEPT);
       scan.Scan();
       require(scan.lookarounds_.values.size()==expected.size());
       for(size_t i=0;i<expected.size();++i) {
        const auto& a=scan.lookarounds_.values[i];const auto& e=expected[i];
        require(a.match_pc==e.match_pc && a.capture_pc==e.capture_pc && a.type==e.type);
       }
       require(scan.only_captureless_lookbehinds_==simple && scan.filter_groups_pc_==filter && scan.quantifier_count_==6);++checks;
      }
     }
    }
   } while(std::next_permutation(order.begin(),order.end()));
  }
  Interpreter empty;empty.bytecode_.values.push_back({});empty.Scan();
  require(empty.lookarounds_.length()==0 && !empty.filter_groups_pc_ && empty.quantifier_count_==0 && empty.only_captureless_lookbehinds_);++checks;
 }
 std::printf("PASS: %u lookaround order, capture, gap and boundary checks\n",checks);
}
