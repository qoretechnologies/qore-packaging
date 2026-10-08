# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil
src=Path('work/nodejs24-source-1/node-v24.18.1');out=Path('work/node-arm-regexp-control-20261008');out.mkdir()
extracts=[]
def extract(path,start,end):
 s=(src/path).read_text();i=s.index(start);body=s[i:s.index(end,i)].rstrip()
 extracts.append({'file':path,'line':s[:i].count('\n')+1,'body':body,'sha256':hashlib.sha256(body.encode()).hexdigest()})
 return body
klass=extract('deps/v8/src/regexp/regexp-ast.h','enum class StandardCharacterSet : char {','\n\n// Represents code points')
body=extract('deps/v8/src/regexp/arm64/regexp-macro-assembler-arm64.cc','bool RegExpMacroAssemblerARM64::CheckSpecialClassRanges(','\nvoid RegExpMacroAssemblerARM64::Fail()')
control=r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Unchanged V8 ARM64 dispatch body; bounded instruction recorder/interpreter.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include <stdexcept>
void require(bool condition) { if (!condition) { std::abort(); } }
'''+klass+r'''
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
'''+body+r'''
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
'''
(out/'control.cc').write_text(control)
(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n')
shutil.copy2(src/'deps/v8/LICENSE',out/'V8-LICENSE')
runner=(Path('work/node-opcode-controls-20261007/run.py').read_text().replace("('native','compressed')","('release','debug')").replace("(['-DV8_COMPRESS_POINTERS'] if mode=='compressed' else [])","(['-DDEBUG'] if mode=='debug' else [])"))
(out/'run.py').write_text(runner)
print(out)
