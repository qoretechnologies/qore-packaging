// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
