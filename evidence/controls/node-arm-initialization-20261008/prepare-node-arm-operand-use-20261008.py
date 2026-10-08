# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil,subprocess
root=Path.cwd();source=root/'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1';out=root/'work/node-arm-operand-use-20261008';out.mkdir()
inl='deps/v8/src/codegen/arm64/macro-assembler-arm64-inl.h';s=(source/inl).read_text();extracts=[];methods=[]
for name in ['Cmp','CompareAndBranch','JumpIfLessThan']:
 a=s.index('void MacroAssembler::'+name+'(');b=s.index('\n}',a)+2;body=s[a:b]
 extracts.append({'file':inl,'line':s[:a].count('\n')+1,'text':body,'sha256':hashlib.sha256(body.encode()).hexdigest()})
 methods.append(body.replace('MacroAssembler::','ProbeAssembler::'))
cpp='''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Actual V8 ARM64 Operand/MemOperand; unchanged selector bodies with an emitter adapter.
#include "src/codegen/arm64/assembler-arm64-inl.h"
#include <array>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <memory>
#include <type_traits>
using namespace v8::internal;
static_assert(std::is_trivially_copyable_v<Operand>);
static_assert(std::is_trivially_copyable_v<MemOperand>);
static size_t checks=0;
static void require(bool ok) { ++checks; if (!ok) { std::fprintf(stderr,"FAIL %zu\\n",checks); std::abort(); } }
struct ProbeAssembler {
 enum class Comparison {None,Plain,Immediate,Shifted,Extended};
 enum class Branch {None,Zero,Nonzero,BitZero,BitNonzero,Conditional};
 Comparison comparison=Comparison::None; Branch branch=Branch::None;
 int64_t immediate=0; unsigned amount=0; Condition condition=al;
 bool allow_macro_instructions() { return true; }
 static Register AppropriateZeroRegFor(const Register& r) { return r.Is64Bits()?xzr:wzr; }
 void CmpPlainRegister(Register,Register) { comparison=Comparison::Plain; }
 void Subs(Register zero,Register left,const Operand& op) {
   require(zero.IsZero() && zero.SizeInBits()==left.SizeInBits());
   if(op.IsImmediate()) {comparison=Comparison::Immediate;immediate=op.ImmediateValue();}
   else if(op.IsShiftedRegister()) {comparison=Comparison::Shifted;amount=op.shift_amount();require(op.reg().is_valid() && op.shift()!=NO_SHIFT);}
   else {comparison=Comparison::Extended;amount=op.shift_amount();require(op.IsExtendedRegister() && op.reg().is_valid() && op.extend()!=NO_EXTEND);}
 }
 void Cbz(Register,Label*) {branch=Branch::Zero;}
 void Cbnz(Register,Label*) {branch=Branch::Nonzero;}
 void Tbz(Register,unsigned bit,Label*) {branch=Branch::BitZero;amount=bit;}
 void Tbnz(Register,unsigned bit,Label*) {branch=Branch::BitNonzero;amount=bit;}
 void B(Condition c,Label*) {branch=Branch::Conditional;condition=c;}
 void Cmp(const Register&,const Operand&);
 void CompareAndBranch(const Register&,const Operand&,Condition,Label*);
 __attribute__((noinline)) void JumpIfLessThan(Register,int32_t,Label*);
};
'''+ '\n'.join(methods)+'''
static void check_immediate(const Operand& op,int64_t value) {
 require(op.IsImmediate() && !op.IsShiftedRegister() && !op.IsExtendedRegister());
 require(op.ImmediateValue()==value);
 MemOperand mem(x3,op);
 require(mem.base()==x3 && mem.IsImmediateOffset() && !mem.IsRegisterOffset());
 require(mem.offset()==value);
}
static void check_register(const Operand& op,Register reg,unsigned amount,bool extended) {
 require(!op.IsImmediate() && op.reg()==reg && op.shift_amount()==amount);
 require(op.IsShiftedRegister()!=extended && op.IsExtendedRegister()==extended);
 MemOperand mem(x3,op);
 require(mem.base()==x3 && !mem.IsImmediateOffset() && mem.IsRegisterOffset());
 require(mem.regoffset()==reg && mem.offset()==0 && mem.shift_amount()==amount);
 if(extended) {require(mem.extend()==op.extend() && mem.shift()==NO_SHIFT);}
 else {require(mem.shift()==LSL && mem.extend()==NO_EXTEND);}
}
enum Mode {kMode_MRI,kMode_MRR};
struct Input {
 int64_t value;Register reg;
 int64_t InputInt64(int n) {require(n==1);return value;}
 Register InputRegister(int n) {require(n==1);return reg;}
};
struct Saved {Operand const offset_;explicit Saved(Operand offset):offset_(offset) {}};
static void store(Mode addressing_mode,Input i) {
  Operand offset(0);
  if (addressing_mode == kMode_MRI) {
    offset = Operand(i.InputInt64(1));
  } else {
    DCHECK_EQ(addressing_mode, kMode_MRR);
    offset = Operand(i.InputRegister(1));
  }
  auto saved=std::make_unique<Saved>(offset);
  if(addressing_mode==kMode_MRI) {check_immediate(offset,i.value);check_immediate(saved->offset_,i.value);}
  else {check_register(offset,i.reg,0,false);check_register(saved->offset_,i.reg,0,false);}
}
int main() {
 std::array<int64_t,13> edges{std::numeric_limits<int64_t>::min(),-4294967296LL,-2147483649LL,-2147483648LL,-4096,-1,0,1,4096,2147483647LL,2147483648LL,4294967295LL,std::numeric_limits<int64_t>::max()};
 for(int64_t value:edges) {
  Operand original(value),assigned(x7);assigned=original;Operand copied=original;
  check_immediate(original,value);check_immediate(assigned,value);check_immediate(copied,value);
  alignas(Operand) unsigned char bytes[sizeof(Operand)];std::memcpy(bytes,&original,sizeof original);
  std::memcpy(&assigned,bytes,sizeof assigned);check_immediate(assigned,value);
  store(kMode_MRI,Input{value,x9});store(kMode_MRR,Input{value,x9});
  for(unsigned amount:{0U,1U,3U,31U,32U,63U}) {
   assigned=Operand(x7,LSL,amount);check_register(assigned,x7,amount,false);
   Operand preserved=assigned;assigned=original;check_immediate(assigned,value);check_register(preserved,x7,amount,false);
  }
  for(Extend ext:{UXTW,SXTW,SXTX}) {
   for(unsigned amount:{0U,1U,4U}) {
    Register reg=ext==SXTX?x9:w9;assigned=Operand(reg,ext,amount);check_register(assigned,reg,amount,true);
    Operand preserved=assigned;assigned=original;check_immediate(assigned,value);check_register(preserved,reg,amount,true);
   }
  }
 }
 for(Register reg:{x2,w2}) {
  for(int32_t value:{std::numeric_limits<int32_t>::min(),-4096,-1,0,1,4096,std::numeric_limits<int32_t>::max()}) {
   ProbeAssembler a;a.JumpIfLessThan(reg,value,nullptr);
   if(value==0) {require(a.comparison==ProbeAssembler::Comparison::None && a.branch==ProbeAssembler::Branch::BitNonzero && a.amount==reg.SizeInBits()-1);}
   else {require(a.comparison==ProbeAssembler::Comparison::Immediate && a.immediate==value && a.branch==ProbeAssembler::Branch::Conditional && a.condition==lt);}
  }
 }
 for(Condition condition:{eq,ne,hs,lo,mi,pl,vs,vc,hi,ls,ge,lt,gt,le,al,nv}) {
  for(int64_t value:{-1LL,0LL,1LL}) {
   ProbeAssembler a;a.CompareAndBranch(x2,Operand(value),condition,nullptr);
   using Branch=ProbeAssembler::Branch;Branch expected=Branch::Conditional;
   if(value==0) {
    switch(condition) {case eq:case ls:expected=Branch::Zero;break;case ne:case hi:expected=Branch::Nonzero;break;case lt:expected=Branch::BitNonzero;break;case ge:expected=Branch::BitZero;break;default:break;}
   }
   require(a.branch==expected);
   require(a.comparison==(expected==Branch::Conditional?ProbeAssembler::Comparison::Immediate:ProbeAssembler::Comparison::None));
  }
 }
 for(Register base:{x2,sp}) {
  for(unsigned amount:{0U,1U,31U,63U}) {
   ProbeAssembler a;a.Cmp(base,Operand(x7,LSL,amount));
   require(a.comparison==((amount==0 && !base.IsSP())?ProbeAssembler::Comparison::Plain:ProbeAssembler::Comparison::Shifted));
  }
  ProbeAssembler a;a.Cmp(base,Operand(w9,SXTW,4));require(a.comparison==ProbeAssembler::Comparison::Extended && a.amount==4);
 }
 std::printf("PASS: %zu actual ARM64 Operand copy/use checks\\n",checks);
}
'''
(out/'control.cc').write_text(cpp);(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n');shutil.copy2(source/'deps/v8/LICENSE',out/'V8-LICENSE')
old=json.loads((root/'results/node-arm-header-codegen-20261008/status.json').read_text());cmd=next(r['command'] for r in old if r['name']=='operand-build');base=cmd[cmd.index('g++'):];base[2:4]=['/control/operand.o','/control/control.cc'];base=[a for a in base if a not in ['-Werror','-c']]
# A second O0 compilation checks optimizer-independent behavior; actual V8 release assertions remain unchanged.
records=[]
for mode,opt in [('optimized','-O2'),('unoptimized','-O0')]:
 args=[a for a in base if not a.startswith('-O')];args[2]='/control/'+mode;args += [opt,'-pthread']
 for step,command in [('compile',args),('normal',['/control/'+mode]),('valgrind',['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','/control/'+mode])]:
  docker=['docker','run','--rm','--network','none','--user','1019:100','-v',str(source)+':/source:ro','-v',str(out)+':/control','-w','/source/out','sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414',*command]
  with (out/(mode+'-'+step+'.log')).open('x') as log:r=subprocess.run(docker,stdout=log,stderr=subprocess.STDOUT)
  records.append({'name':mode+'-'+step,'command':docker,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(records,indent=2)+'\n');r.check_returncode()
