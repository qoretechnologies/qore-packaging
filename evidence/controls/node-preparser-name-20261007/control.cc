// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
template<class Impl> unsigned run(bool preparser) {
 unsigned checks=0;
 for(unsigned repeat=0;repeat<1000;++repeat) {
  for(unsigned name=1;name<=6;++name) {for(auto token:{Token::kLeftParen,Token::kName,Token::kReserved,Token::kInvalid}) {
   for(int flags:{0,1,2}) {for(bool star:{false,true}) {for(unsigned scope=0;scope<8;++scope) {
    for(bool default_export:{false,true}) {
     // All preparser call sites pass false; default exports use Parser only.
     if(preparser&&default_export) {continue;}
     ParserBase<Impl> p;AstRawString symbol{name};auto& s=p.state;s.symbol=&symbol;s.token=token;s.mul=star;
     s.scope_={bool(scope&1),bool(scope&2)};s.strict=scope&4;
     int result=p.ParseHoistableDeclaration(3,flags,nullptr,default_export);
     bool missing=token==Token::kLeftParen&&!default_export;
     require(p.fni_==0 && s.error==(missing||token==Token::kInvalid));
     require(s.declarations==unsigned(!missing) && s.literals==unsigned(!missing));
     if(missing) {require(result==-1 && s.declared==nullptr);}
     else {
      const AstRawString* expected=token==Token::kLeftParen?&s.default_binding:token==Token::kInvalid?&s.empty:&symbol;
      require(result==1 && s.declared==expected);
      require(s.declared_mode==(!(scope&1)||(scope&2)?VariableMode::kLet:VariableMode::kVar));
      int effective=flags|((flags==1&&star)?2:0);
      require(s.function_flags==effective);
      require(s.declared_kind==(!(scope&4)&&!(scope&1)&&effective==0?SLOPPY_BLOCK_FUNCTION_VARIABLE:NORMAL_VARIABLE));
      require(s.validity==(token==Token::kLeftParen?kSkipFunctionNameCheck:token==Token::kReserved?kFunctionNameIsStrictReserved:kFunctionNameValidityUnknown));
     }
     ++checks;
    }
   }}}
  }}
 }
 return checks;
}
int main() {
 unsigned pre=run<PreParser>(true),full=run<Parser>(false);
 std::printf("PASS: %u preparser and %u full-parser declaration-path checks\n",pre,full);
}
