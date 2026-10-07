# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil
root=Path('work/node-obs-diagnostic-20261006/node-v24.18.1');out=Path('work/node-preparser-name-controls-20261007');out.mkdir(exist_ok=True)
extracts=[]
def extract(path,start,end):
 s=(root/path).read_text();a=s.index(start);b=s.index(end,a);body=s[a:b];extracts.append(dict(file=path,line=s[:a].count('\n')+1,body=body,sha256=hashlib.sha256(body.encode()).hexdigest()));return body
identifier=extract('deps/v8/src/parsing/preparser.h','class PreParserIdentifier {','\nclass PreParserExpression {')
body=extract('deps/v8/src/parsing/parser-base.h','template <typename Impl>\ntypename ParserBase<Impl>::StatementT\nParserBase<Impl>::ParseHoistableDeclaration(\n    int pos,','\ntemplate <typename Impl>\ntypename ParserBase<Impl>::StatementT ParserBase<Impl>::ParseClassDeclaration')
extract('deps/v8/src/parsing/preparser.cc','PreParserIdentifier PreParser::GetIdentifier() const {','\nPreParser::PreParseResult')
extract('deps/v8/src/parsing/preparser.h','  V8_INLINE PreParserIdentifier EmptyIdentifierString() const {','\n  V8_INLINE bool IsEmptyIdentifier')
extract('deps/v8/src/parsing/preparser.h','  V8_INLINE static void GetDefaultStrings(','\n  // Functions for encapsulating')
extract('deps/v8/src/parsing/parser.h','  V8_INLINE void GetDefaultStrings(','\n  // Functions for encapsulating')
for path in ('deps/v8/src/parsing/parser-base.h','deps/v8/src/parsing/parser.cc'):
 s=(root/path).read_text();lines=s.splitlines(True)
 for i,line in enumerate(lines):
  if 'ParseHoistableDeclaration(' in line or 'ParseAsyncFunctionDeclaration(' in line:
   if ('return ' in line or 'result = ' in line):
    a=max(0,i-2);text=''.join(lines[a:i+2]);extracts.append(dict(file=path,line=a+1,body=text,sha256=hashlib.sha256(text.encode()).hexdigest()))
(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n')
(out/'control.h').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <vector>
inline void require(bool v) {if(!v) {std::abort();}}
#ifdef DEBUG
#define DCHECK_IMPLIES(a,b) require(!(a)||(b))
#else
#define DCHECK_IMPLIES(a,b) ((void)0)
#endif
namespace base {template<class T> bool IsInRange(T v,T a,T b) {return v>=a&&v<=b;}}
struct AstRawString {unsigned id;};
'''+identifier+r'''
template<class T> using ZonePtrList=std::vector<T>;
struct Token {enum Value {kLeftParen,kName,kReserved,kInvalid,kMul};static bool IsStrictReservedWord(Value v) {return v==kReserved;}};
struct ParseFunctionFlag {static constexpr int kIsNormal=0,kIsAsync=1,kIsGenerator=2;};
using ParseFunctionFlags=int;
enum FunctionNameValidity {kSkipFunctionNameCheck,kFunctionNameIsStrictReserved,kFunctionNameValidityUnknown};
enum class VariableMode {kLet,kVar};
enum VariableKind {SLOPPY_BLOCK_FUNCTION_VARIABLE,NORMAL_VARIABLE};
enum class FunctionSyntaxKind {kDeclaration};
enum class MessageTemplate {kMissingFunctionName};
using FunctionKind=int;
inline FunctionKind FunctionKindFor(int flags) {return flags;}
inline bool is_sloppy(bool strict) {return !strict;}
struct Scope {
 bool declaration=false,module=false;
 bool is_declaration_scope() const {return declaration;}
 bool is_module_scope() const {return module;}
};
struct Scanner {int location() const {return 7;}};
struct FuncNameInferrerState {
 unsigned* depth;explicit FuncNameInferrerState(unsigned* d):depth(d) {++*depth;}
 ~FuncNameInferrerState() {--*depth;}
};
struct State {
 Token::Value token=Token::kName;bool mul=false,strict=false,error=false;
 Scope scope_;Scanner scanner_;
 const AstRawString* symbol=nullptr;
 AstRawString empty{0},default_name{100},default_binding{101};
 unsigned declarations=0,literals=0;
 const AstRawString* declared=nullptr;
 VariableMode declared_mode=VariableMode::kVar;
 VariableKind declared_kind=NORMAL_VARIABLE;
 FunctionNameValidity validity=kFunctionNameValidityUnknown;
 int function_flags=-1;
};
struct PreParser:State {
 using IdentifierT=PreParserIdentifier;
 static void GetDefaultStrings(PreParserIdentifier*,PreParserIdentifier*) {}
 PreParserIdentifier ParseIdentifier();
 static int NullStatement() {return -1;}
 void PushEnclosingName(const PreParserIdentifier&) {}
 int ParseFunctionLiteral(const PreParserIdentifier&,int,FunctionNameValidity validity_,int flags,int,FunctionSyntaxKind,bool,void*) {
  ++literals;validity=validity_;function_flags=flags;return 1;
 }
 int DeclareFunction(const PreParserIdentifier& name,int,VariableMode mode,VariableKind kind,int,int,ZonePtrList<const AstRawString>* names) {
  require(names==nullptr);declared=name.string_;require(declared);declared_mode=mode;declared_kind=kind;++declarations;return 1;
 }
};
struct Parser:State {
 using IdentifierT=const AstRawString*;
 void GetDefaultStrings(const AstRawString** name,const AstRawString** binding) {*name=&default_name;*binding=&default_binding;}
 const AstRawString* ParseIdentifier() {if(token==Token::kInvalid) {error=true;return &empty;}return symbol;}
 static int NullStatement() {return -1;}
 void PushEnclosingName(const AstRawString*) {}
 int ParseFunctionLiteral(const AstRawString*,int,FunctionNameValidity validity_,int flags,int,FunctionSyntaxKind,bool,void*) {
  ++literals;validity=validity_;function_flags=flags;return 1;
 }
 int DeclareFunction(const AstRawString* name,int,VariableMode mode,VariableKind kind,int,int,ZonePtrList<const AstRawString>*) {
  declared=name;require(declared);declared_mode=mode;declared_kind=kind;++declarations;return 1;
 }
};
template<class Impl> struct ParserBase {
 using IdentifierT=typename Impl::IdentifierT;
 using StatementT=int;using FunctionLiteralT=int;
 Impl state;unsigned fni_=0;
 Impl* impl() {return &state;}
 void CheckStackOverflow() {}
 bool Check(Token::Value t) {return t==Token::kMul&&state.mul;}
 Token::Value peek() const {return state.token;}
 IdentifierT ParseIdentifier() {return state.ParseIdentifier();}
 void ReportMessage(MessageTemplate) {state.error=true;}
 Scope* scope() {return &state.scope_;}
 Scanner* scanner() {return &state.scanner_;}
 bool language_mode() const {return state.strict;}
 int end_position() const {return 11;}
 StatementT ParseHoistableDeclaration(int,ParseFunctionFlags,ZonePtrList<const AstRawString>*,bool);
};
'''+body)
(out/'helper.cc').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
PreParserIdentifier PreParser::ParseIdentifier() {
  PreParserIdentifier result=PreParserIdentifier::Default();
  if(token==Token::kInvalid) {error=true;result.string_=&empty;}
  else {require(symbol);result.string_=symbol;}
  return result;
}
''')
(out/'control.cc').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
''')
shutil.copy2(root/'deps/v8/LICENSE',out/'V8-LICENSE');shutil.copy2('work/node-wasm-grow-controls-20261007/run.py',out/'run.py')
print('Prepared unchanged declaration parser and real preparser identifier layout.')
