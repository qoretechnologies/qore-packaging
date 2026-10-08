# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib,hashlib,json,shutil,subprocess
root=Path.cwd();source=root/'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1';out=root/'work/node-arm-initialization-20261008';out.mkdir()
rel='deps/v8/src/codegen/arm64/assembler-arm64.h';original=(source/rel).read_text()
old='  Shift shift_;\n  Extend extend_;\n  unsigned shift_amount_;'
assert original.count(old)==2
fixed=original.replace(old,'  // Immediate operands are copied by value; keep inactive members initialized.\n  Shift shift_ = NO_SHIFT;\n  Extend extend_ = NO_EXTEND;\n  unsigned shift_amount_ = 0;')
(out/'assembler-arm64.h').write_text(fixed)
(out/'nodejs24-arm-operand-initialization.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),fixed.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel)))
cpp=r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// White-box constructor regression, compiled with -fno-access-control only for this fixture.
// Inspect field representations via memcpy; primed storage makes failures deterministic.
#include "src/codegen/arm64/assembler-arm64-inl.h"
#include <array>
#include <cstdio>
#include <cstring>
#include <limits>
#include <memory>
#include <new>
#include <type_traits>
using namespace v8::internal;
static_assert(std::is_trivially_copyable_v<Operand>);
static_assert(std::is_trivially_copyable_v<MemOperand>);
static unsigned checks=0;
template<typename Field> bool same_bits(const Field& field,Field expected) {
  return std::memcmp(static_cast<const void*>(&field),static_cast<const void*>(&expected),sizeof(Field))==0;
}
template<class T> bool fields(const T& obj,Shift shift,Extend extend,unsigned amount) {
 ++checks;
 return same_bits(obj.shift_,shift)&&same_bits(obj.extend_,extend)&&same_bits(obj.shift_amount_,amount);
}
template<class T,class Maker> bool construct(Maker make,Shift shift,Extend ext,unsigned amount) {
 alignas(T) unsigned char storage[sizeof(T)];std::memset(storage,0xa5,sizeof storage);
 T* object=make(static_cast<void*>(storage));
 bool ok=fields(*object,shift,ext,amount);
 if(ok) {
   T copy=*object;ok=fields(copy,shift,ext,amount);
   T assigned=*object;assigned=copy;ok=fields(assigned,shift,ext,amount)&&ok;
 }
 std::destroy_at(object);
 return ok;
}
int main(int argc,char** argv) {
 bool mem_only=argc==2 && std::strcmp(argv[1],"mem")==0;
 std::array<int64_t,9> edges{std::numeric_limits<int64_t>::min(),-2147483649LL,-2147483648LL,-1,0,1,2147483647LL,2147483648LL,std::numeric_limits<int64_t>::max()};
 for(int64_t value:edges) {
  if(!mem_only) {
   if(!construct<Operand>([&](void* p){return new(p) Operand(value);},NO_SHIFT,NO_EXTEND,0)) {std::fprintf(stderr,"FAIL Operand immediate inactive fields\n");return 1;}
   if(!construct<Operand>([&](void* p){return new(p) Operand(value,RelocInfo::NO_INFO);},NO_SHIFT,NO_EXTEND,0)) {std::fprintf(stderr,"FAIL Operand reloc inactive fields\n");return 1;}
  }
  for(AddrMode mode:{Offset,PreIndex,PostIndex}) {
   if(!construct<MemOperand>([&](void* p){return new(p) MemOperand(x3,Operand(value),mode);},NO_SHIFT,NO_EXTEND,0)) {std::fprintf(stderr,"FAIL MemOperand immediate inactive fields\n");return 1;}
   if(!construct<MemOperand>([&](void* p){return new(p) MemOperand(x3,value,mode);},NO_SHIFT,NO_EXTEND,0)) {return 1;}
  }
 }
 if(!construct<MemOperand>([](void* p){return new(p) MemOperand();},NO_SHIFT,NO_EXTEND,0)) {return 1;}
 for(Shift shift:{LSL,LSR,ASR,ROR}) {
  for(unsigned amount:{0U,1U,31U,32U,63U}) {
   if(!construct<Operand>([&](void* p){return new(p) Operand(x7,shift,amount);},shift,NO_EXTEND,amount)) {return 1;}
  }
 }
 for(Extend ext:{UXTB,UXTH,UXTW,UXTX,SXTB,SXTH,SXTW,SXTX}) {
  for(unsigned amount:{0U,1U,4U}) {
   if(!construct<Operand>([&](void* p){return new(p) Operand(x9,ext,amount);},NO_SHIFT,ext,amount)) {return 1;}
  }
 }
 for(unsigned amount:{0U,1U,3U,31U,32U,63U}) {
  for(AddrMode mode:{Offset,PostIndex}) {
   if(!construct<MemOperand>([&](void* p){return new(p) MemOperand(x3,Operand(x7,LSL,amount),mode);},LSL,NO_EXTEND,amount)) {return 1;}
  }
  if(!construct<MemOperand>([&](void* p){return new(p) MemOperand(x3,x7,LSL,amount);},LSL,NO_EXTEND,amount)) {return 1;}
 }
 for(Extend ext:{UXTW,SXTW,SXTX}) {
  for(unsigned amount:{0U,1U,4U}) {
   if(!construct<MemOperand>([&](void* p){return new(p) MemOperand(x3,Operand(x9,ext,amount));},NO_SHIFT,ext,amount)) {return 1;}
   if(!construct<MemOperand>([&](void* p){return new(p) MemOperand(x3,x9,ext,amount);},NO_SHIFT,ext,amount)) {return 1;}
  }
 }
 std::printf("PASS: %u constructor/copy field checks\n",checks);
}
'''
(out/'constructor-test.cc').write_text(cpp)
shutil.copy2(root/'work/node-arm-operand-use-final-20261008/control.cc',out/'use-test.cc')
shutil.copy2(source/'deps/v8/LICENSE',out/'V8-LICENSE')
old=json.loads((root/'results/node-arm-header-codegen-20261008/status.json').read_text());cmd=next(r['command'] for r in old if r['name']=='operand-build');base=cmd[cmd.index('g++'):];base=[a for a in base if a!='-c'];records=[]
for kind in ['original','fixed']:
 for mode,opt in [('optimized','-O2'),('debug-optimized','-Og')]:
  for test in ['constructor','use'] if kind=='fixed' else ['constructor']:
   stem=kind+'-'+mode+'-'+test
   args=[a for a in base if not a.startswith('-O')];args[2:4]=['/control/'+stem,'/control/'+test+'-test.cc'];args += [opt,'-pthread']
   if test=='constructor':args.append('-fno-access-control')
   commands=[('compile',args,0)]
   if kind=='original':commands += [('operand-negative',['/control/'+stem],1),('mem-negative',['/control/'+stem,'mem'],1)]
   else:commands += [('normal',['/control/'+stem],0),('valgrind',['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','/control/'+stem],0)]
   for step,command,expected in commands:
    docker=['docker','run','--rm','--network','none','--user','1019:100','-v',str(source)+':/source:ro','-v',str(out)+':/control']
    if kind=='fixed':docker += ['-v',str(out/'assembler-arm64.h')+':/source/'+rel+':ro']
    docker += ['-w','/source/out','sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414',*command]
    with (out/(stem+'-'+step+'.log')).open('x') as log:r=subprocess.run(docker,stdout=log,stderr=subprocess.STDOUT)
    records.append({'name':stem+'-'+step,'command':docker,'exit_code':r.returncode,'expected_exit':expected});(out/'status.json').write_text(json.dumps(records,indent=2)+'\n');assert r.returncode==expected,records[-1]
print('Constructor fix and original-source negative controls qualified.')
