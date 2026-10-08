// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Unchanged V8 ARM64 dispatch body; bounded instruction recorder/interpreter.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <stdexcept>
void require(bool condition) { if (!condition) { std::abort(); } }
enum class StandardCharacterSet : char {
  kWhitespace = 's',         // Like /\s/.
  kNotWhitespace = 'S',      // Like /\S/.
  kWord = 'w',               // Like /\w/.
  kNotWord = 'W',            // Like /\W/.
  kDigit = 'd',              // Like /\d/.
  kNotDigit = 'D',           // Like /\D/.
  kLineTerminator = 'n',     // The inverse of /./.
  kNotLineTerminator = '.',  // Like /./.
  kEverything = '*',         // Matches every character, like /./s.
};
enum Mode {LATIN1,UC16};
enum Condition {eq,ne,hi,ls};
constexpr unsigned ZFlag=4,NoFlag=0;
struct Register {unsigned index;};
constexpr Register w10{10},x10{10};
struct Label {int id=-1;};
enum Extend {UXTW};
struct MemOperand {Register base,index;Extend extend;};
struct ExternalReference { static ExternalReference re_word_character_map() {return {};} };
struct RegExpMacroAssemblerARM64 {
 enum class Op {cmp,ccmp,branch,sub,mov,load};
 struct Instruction {Op op;unsigned reg;uint32_t imm;unsigned flags;Condition cond;int target;};
 Mode mode_; std::vector<Instruction> instructions;std::vector<size_t> labels;
 explicit RegExpMacroAssemblerARM64(Mode mode):mode_(mode) {}
 Register current_character() const {return {0};}
 int label(Label* label) {
  if(label==nullptr) {return -1;}
  if(label->id<0) {label->id=static_cast<int>(labels.size());labels.push_back(SIZE_MAX);}
  return label->id;
 }
 void Bind(Label* target) {int i=label(target);require(i>=0);require(labels.at(static_cast<size_t>(i))==SIZE_MAX);labels.at(static_cast<size_t>(i))=instructions.size();}
 void Cmp(Register reg,uint32_t imm) {instructions.push_back({Op::cmp,reg.index,imm,0,eq,0});}
 void Ccmp(Register reg,uint32_t imm,unsigned flags,Condition cond) {instructions.push_back({Op::ccmp,reg.index,imm,flags,cond,0});}
 void B(Condition cond,Label* target) {instructions.push_back({Op::branch,0,0,0,cond,label(target)});}
 void Sub(Register dest,Register src,uint32_t imm) {require(dest.index==10&&src.index==0);instructions.push_back({Op::sub,dest.index,imm,0,eq,0});}
 void Mov(Register dest,ExternalReference) {require(dest.index==10);instructions.push_back({Op::mov,dest.index,0,0,eq,0});}
 void Ldrb(Register dest,MemOperand mem) {require(dest.index==10&&mem.base.index==10&&mem.index.index==0&&mem.extend==UXTW);instructions.push_back({Op::load,dest.index,0,0,eq,0});}
 void CompareAndBranchOrBacktrack(Register reg,uint32_t imm,Condition cond,Label* target) {Cmp(reg,imm);B(cond,target);}
 void BranchOrBacktrack(Condition cond,Label* target) {B(cond,target);}
 __attribute__((noinline)) bool CheckSpecialClassRanges(StandardCharacterSet type,Label* on_no_match);
 bool execute(uint32_t c) const {
  require(c <= (mode_==LATIN1?255u:65535u));
  std::array<uint32_t,11> regs{};regs[0]=c;bool zero=false,carry=false;
  auto condition=[&](Condition cond) {switch(cond) {case eq:return zero;case ne:return !zero;case hi:return carry&&!zero;case ls:return !carry||zero;} std::abort();};
  auto compare=[&](uint32_t x,uint32_t y) {zero=x==y;carry=x>=y;};
  size_t pc=0,steps=0;
  while(pc<instructions.size()) {
   require(++steps<64);const auto& i=instructions.at(pc++);
   switch(i.op) {
    case Op::cmp:compare(regs.at(i.reg),i.imm);break;
    case Op::ccmp:if(condition(i.cond)) {compare(regs.at(i.reg),i.imm);} else {zero=(i.flags&4)!=0;carry=(i.flags&2)!=0;}break;
    case Op::branch:if(condition(i.cond)) {if(i.target<0) {return false;}pc=labels.at(static_cast<size_t>(i.target));require(pc<=instructions.size());}break;
    case Op::sub:regs.at(i.reg)=regs[0]-i.imm;break;
    case Op::mov:regs.at(i.reg)=0;break;
    case Op::load:require(regs[0]<256);regs.at(i.reg)=(regs[0]>='0'&&regs[0]<='9')||(regs[0]>='A'&&regs[0]<='Z')||(regs[0]>='a'&&regs[0]<='z')||regs[0]=='_';break;
   }
  }
  return true;
 }
};
#define __ this->
bool RegExpMacroAssemblerARM64::CheckSpecialClassRanges(
    StandardCharacterSet type, Label* on_no_match) {
  // Range checks (c in min..max) are generally implemented by an unsigned
  // (c - min) <= (max - min) check
  // TODO(jgruber): No custom implementation (yet): s(UC16), S(UC16).
  switch (type) {
    case StandardCharacterSet::kWhitespace:
      // Match space-characters.
      if (mode_ == LATIN1) {
        // One byte space characters are '\t'..'\r', ' ' and \u00a0.
        Label success;
        // Check for ' ' or 0x00A0.
        __ Cmp(current_character(), ' ');
        __ Ccmp(current_character(), 0x00A0, ZFlag, ne);
        __ B(eq, &success);
        // Check range 0x09..0x0D.
        __ Sub(w10, current_character(), '\t');
        CompareAndBranchOrBacktrack(w10, '\r' - '\t', hi, on_no_match);
        __ Bind(&success);
        return true;
      }
      return false;
    case StandardCharacterSet::kNotWhitespace:
      // The emitted code for generic character classes is good enough.
      return false;
    case StandardCharacterSet::kDigit:
      // Match ASCII digits ('0'..'9').
      __ Sub(w10, current_character(), '0');
      CompareAndBranchOrBacktrack(w10, '9' - '0', hi, on_no_match);
      return true;
    case StandardCharacterSet::kNotDigit:
      // Match ASCII non-digits.
      __ Sub(w10, current_character(), '0');
      CompareAndBranchOrBacktrack(w10, '9' - '0', ls, on_no_match);
      return true;
    case StandardCharacterSet::kNotLineTerminator: {
      // Match non-newlines (not 0x0A('\n'), 0x0D('\r'), 0x2028 and 0x2029)
      // Here we emit the conditional branch only once at the end to make branch
      // prediction more efficient, even though we could branch out of here
      // as soon as a character matches.
      __ Cmp(current_character(), 0x0A);
      __ Ccmp(current_character(), 0x0D, ZFlag, ne);
      if (mode_ == UC16) {
        __ Sub(w10, current_character(), 0x2028);
        // If the Z flag was set we clear the flags to force a branch.
        __ Ccmp(w10, 0x2029 - 0x2028, NoFlag, ne);
        // ls -> !((C==1) && (Z==0))
        BranchOrBacktrack(ls, on_no_match);
      } else {
        BranchOrBacktrack(eq, on_no_match);
      }
      return true;
    }
    case StandardCharacterSet::kLineTerminator: {
      // Match newlines (0x0A('\n'), 0x0D('\r'), 0x2028 and 0x2029)
      // We have to check all 4 newline characters before emitting
      // the conditional branch.
      __ Cmp(current_character(), 0x0A);
      __ Ccmp(current_character(), 0x0D, ZFlag, ne);
      if (mode_ == UC16) {
        __ Sub(w10, current_character(), 0x2028);
        // If the Z flag was set we clear the flags to force a fall-through.
        __ Ccmp(w10, 0x2029 - 0x2028, NoFlag, ne);
        // hi -> (C==1) && (Z==0)
        BranchOrBacktrack(hi, on_no_match);
      } else {
        BranchOrBacktrack(ne, on_no_match);
      }
      return true;
    }
    case StandardCharacterSet::kWord: {
      if (mode_ != LATIN1) {
        // Table is 256 entries, so all Latin1 characters can be tested.
        CompareAndBranchOrBacktrack(current_character(), 'z', hi, on_no_match);
      }
      ExternalReference map = ExternalReference::re_word_character_map();
      __ Mov(x10, map);
      __ Ldrb(w10, MemOperand(x10, current_character(), UXTW));
      CompareAndBranchOrBacktrack(w10, 0, eq, on_no_match);
      return true;
    }
    case StandardCharacterSet::kNotWord: {
      Label done;
      if (mode_ != LATIN1) {
        // Table is 256 entries, so all Latin1 characters can be tested.
        __ Cmp(current_character(), 'z');
        __ B(hi, &done);
      }
      ExternalReference map = ExternalReference::re_word_character_map();
      __ Mov(x10, map);
      __ Ldrb(w10, MemOperand(x10, current_character(), UXTW));
      CompareAndBranchOrBacktrack(w10, 0, ne, on_no_match);
      __ Bind(&done);
      return true;
    }
    case StandardCharacterSet::kEverything:
      // Match any character.
      return true;
  }
}
#undef __
bool expected(StandardCharacterSet set,uint32_t c) {
 const bool word=(c>='0'&&c<='9')||(c>='A'&&c<='Z')||(c>='a'&&c<='z')||c=='_';
 const bool digit=c>='0'&&c<='9';
 const bool line=c==10||c==13||c==0x2028||c==0x2029;
 const bool space=(c>=9&&c<=13)||c==32||c==160||c==0x1680||(c>=0x2000&&c<=0x200a)||c==0x2028||c==0x2029||c==0x202f||c==0x205f||c==0x3000||c==0xfeff;
 switch(set) {
  case StandardCharacterSet::kWhitespace:return space;
  case StandardCharacterSet::kNotWhitespace:return !space;
  case StandardCharacterSet::kWord:return word;
  case StandardCharacterSet::kNotWord:return !word;
  case StandardCharacterSet::kDigit:return digit;
  case StandardCharacterSet::kNotDigit:return !digit;
  case StandardCharacterSet::kLineTerminator:return line;
  case StandardCharacterSet::kNotLineTerminator:return !line;
  case StandardCharacterSet::kEverything:return true;
 }
 std::abort();
}
int main() {
 const std::array sets{StandardCharacterSet::kWhitespace,StandardCharacterSet::kNotWhitespace,
  StandardCharacterSet::kWord,StandardCharacterSet::kNotWord,StandardCharacterSet::kDigit,
  StandardCharacterSet::kNotDigit,StandardCharacterSet::kLineTerminator,
  StandardCharacterSet::kNotLineTerminator,StandardCharacterSet::kEverything};
 unsigned checks=0,unsupported=0;
 for(auto mode:{LATIN1,UC16}) {
  for(auto set:sets) {
   RegExpMacroAssemblerARM64 asm_(mode);
   bool specialized=asm_.CheckSpecialClassRanges(set,nullptr);
   bool should_specialize=set!=StandardCharacterSet::kNotWhitespace && !(set==StandardCharacterSet::kWhitespace&&mode==UC16);
   require(specialized==should_specialize);++checks;
   if(!specialized) {require(asm_.instructions.empty());++unsupported;continue;}
   for(uint32_t c=0;c<=(mode==LATIN1?255u:65535u);++c) {
    if(asm_.execute(c)!=expected(set,c)) {std::fprintf(stderr,"mismatch mode=%d set=%c char=%u\n",mode,static_cast<char>(set),c);return 1;}++checks;
   }
   // Also exercise an explicit no-match label rather than implicit backtracking.
   RegExpMacroAssemblerARM64 explicit_(mode);Label fail;
   require(explicit_.CheckSpecialClassRanges(set,&fail));
   // A final comparison always takes the rejection edge after success; this
   // checks all label IDs are valid and bound without storing stack pointers.
   explicit_.Cmp({0},0);explicit_.B(eq,nullptr);explicit_.B(ne,nullptr);
   explicit_.Bind(&fail);
   for(uint32_t c:{0u,9u,10u,13u,32u,47u,48u,57u,58u,65u,90u,95u,97u,122u,123u,160u,255u}) {
    require(explicit_.execute(c)==!expected(set,c));++checks;
   }
  }
 }
 require(unsupported==3);
 std::printf("PASS: %u ARM64 class dispatch/emission checks; %u generic fallback cases\n",checks,unsupported);
}
