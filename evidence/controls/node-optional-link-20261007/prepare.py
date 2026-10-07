# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil
root=Path('work/node-obs-diagnostic-20261006/node-v24.18.1');out=Path('work/node-optional-link-controls-20261007');out.mkdir()
path='deps/v8/src/parsing/parser-base.h';s=(root/path).read_text();a=s.index('  bool optional_chaining = false;');b=s.index('\n}\n\ntemplate <typename Impl>',a);body=s[a:b]
(out/'source-extracts.json').write_text(json.dumps([dict(file=path,line=s[:a].count('\n')+1,body=body,sha256=hashlib.sha256(body.encode()).hexdigest())],indent=2)+'\n')
(out/'control.h').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#pragma once
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <vector>
inline void require(bool value) {if(!value) {std::abort();}}
#ifdef DEBUG
#define DCHECK(x) require(bool(x))
#else
#define DCHECK(x) ((void)0)
#endif
struct Token {
 enum Value {kQuestionPeriod,kLeftBracket,kRightBracket,kPeriod,kLeftParen,kRightParen,kName,kPrivate,kTemplate,kSpread,kComma,kEos};
 static bool IsPropertyOrCall(Value token) {return token==kQuestionPeriod||token==kLeftBracket||token==kPeriod||token==kLeftParen||token==kTemplate;}
 static bool IsCallable(Value token) {return token==kName||token==kPrivate;}
 static bool IsTemplate(Value token) {return token==kTemplate;}
};
struct SourceRange {int begin,end;SourceRange(int b,int e):begin(b),end(e) {} bool operator==(const SourceRange&) const=default;};
struct Location {int beg_pos;};
struct Lexeme {Token::Value token;int position;};
struct Scanner {
 std::vector<Lexeme> input;size_t next=0;Token::Value previous=Token::kName;int previous_position=-1;
 Location peek_location() const {require(next<input.size());return {input[next].position};}
 Token::Value current_token() const {return previous;}
};
struct Expression {
 bool literal=false,eager=false,chain=false;
 bool IsFunctionLiteral() const {return literal;}
 Expression* AsFunctionLiteral() {require(literal);return this;}
 void SetShouldEagerCompile() {eager=true;}
};
using ExpressionT=Expression*;
struct ExpressionListT:std::vector<Expression*> {explicit ExpressionListT(void*) {}};
enum class MessageTemplate {kOptionalChainingNoTemplate};
struct Factory {
 std::vector<std::unique_ptr<Expression>> nodes;
 std::vector<bool> optional;
 unsigned calls=0,properties=0,spreads=0;
 Expression* make() {auto p=std::make_unique<Expression>();auto* result=p.get();nodes.push_back(std::move(p));return result;}
 Expression* NewProperty(Expression*,Expression*,int,bool is_optional) {++properties;optional.push_back(is_optional);return make();}
 Expression* NewCall(Expression*,const ExpressionListT&,int,bool spread,int,bool is_optional) {++calls;spreads+=spread;optional.push_back(is_optional);return make();}
 Expression* NewOptionalChain(Expression*) {auto* result=make();result->chain=true;return result;}
};
struct Inference {unsigned removed=0;void RemoveLastFunction() {++removed;}};
struct Parser {
 Scanner scan;Factory storage;Inference fni_;bool error=false;unsigned accept_depth=0;
 std::vector<SourceRange> ranges;
 struct AcceptINScope {Parser* p;AcceptINScope(Parser* parser,bool):p(parser) {++p->accept_depth;}~AcceptINScope() {--p->accept_depth;}};
 Token::Value peek() const;
 Scanner* scanner() {return &scan;}
 int position() const {return scan.previous_position;}
 int peek_position() const {return scan.peek_location().beg_pos;}
 int end_position() const {return scan.previous_position+1;}
 void Consume(Token::Value token) {require(peek()==token);Next();}
 Token::Value Next() {auto t=peek();scan.previous=t;scan.previous_position=scan.input[scan.next].position;++scan.next;return t;}
 Parser* impl() {return this;}
 Factory* factory() {return &storage;}
 void ReportUnexpectedToken(Token::Value) {error=true;}
 void ReportMessageAt(Location,MessageTemplate) {error=true;}
 Expression* FailureExpression() {return nullptr;}
 Expression* ParsePropertyOrPrivatePropertyName() {require(peek()==Token::kName||peek()==Token::kPrivate);Next();return storage.make();}
 Expression* ParseExpressionCoverGrammar() {return ParsePropertyOrPrivatePropertyName();}
 void Expect(Token::Value token) {Consume(token);}
 void* pointer_buffer() {return nullptr;}
 void ParseArguments(ExpressionListT* args,bool* spread) {
  Consume(Token::kLeftParen);*spread=false;
  if(peek()!=Token::kRightParen) {
   if(peek()==Token::kSpread) {Consume(Token::kSpread);*spread=true;}
   args->push_back(ParseExpressionCoverGrammar());
  }
  Consume(Token::kRightParen);
 }
 void* scope() {return nullptr;}
 bool CheckPossibleEvalCall(Expression*,bool,void*) {return false;}
 int GetNextInfoId() {return 1;}
 Expression* ParseTemplateLiteral(Expression*,int,bool) {Consume(Token::kTemplate);return storage.make();}
 void RecordExpressionSourceRange(Expression*,SourceRange range) {ranges.push_back(range);}
 Expression* Parse(ExpressionT result);
};
''')
(out/'helper.cc').write_text('''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
Token::Value Parser::peek() const {require(scan.next<scan.input.size());return scan.input[scan.next].token;}
''')
(out/'control.cc').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
Expression* Parser::Parse(ExpressionT result) {
'''+body+r'''
}
int main() {
 unsigned checks=0;
 for(unsigned repeat=0;repeat<10;++repeat) {
  unsigned combinations=1;
  for(unsigned length=1;length<=4;++length) {
   combinations*=8;
   for(unsigned code=0;code<combinations;++code) {for(bool function_literal:{false,true}) {
    Parser p;int pos=repeat*101;
    auto add=[&](Token::Value token) {p.scan.input.push_back({token,pos++});};
    std::vector<SourceRange> expected_ranges;std::vector<bool> expected_optional;
    unsigned rest=code,calls=0,properties=0,spreads=0;bool chain=false,error=false;
    for(unsigned i=0;i<length;++i) {
     unsigned op=rest%8;rest/=8;bool optional=op>=4&&op<=6;int begin=pos;
     if(optional) {add(Token::kQuestionPeriod);}
     switch(op) {
      case 0:add(Token::kPeriod);add(Token::kName);break;
      case 1:add(Token::kLeftBracket);add(Token::kName);add(Token::kRightBracket);break;
      case 2:add(Token::kLeftParen);add(Token::kRightParen);break;
      case 3:add(Token::kLeftParen);add(Token::kSpread);add(Token::kName);add(Token::kRightParen);break;
      case 4:add(i%2?Token::kPrivate:Token::kName);break;
      case 5:add(Token::kLeftBracket);add(Token::kName);add(Token::kRightBracket);break;
      case 6:add(Token::kLeftParen);add(Token::kName);add(Token::kRightParen);break;
      case 7:add(Token::kTemplate);break;
     }
     if(error) {continue;}
     if(op==7&&chain) {error=true;continue;}
     if(op!=7) {expected_optional.push_back(optional);}
     calls+=op==2||op==3||op==6;spreads+=op==3;properties+=op==0||op==1||op==4||op==5;
     if(optional) {expected_ranges.emplace_back(begin,pos);chain=true;}
    }
    add(Token::kEos);auto* input=p.storage.make();input->literal=function_literal;
    p.scan.previous=function_literal?Token::kRightParen:Token::kName;
    auto* result=p.Parse(input);
    require(p.error==error && (result==nullptr)==error && p.accept_depth==0);
    require(p.ranges==expected_ranges && p.storage.optional==expected_optional);
    require(p.storage.calls==calls&&p.storage.properties==properties&&p.storage.spreads==spreads&&p.fni_.removed==calls);
    if(result) {require(result->chain==chain);}
    ++checks;
   }}
  }
  for(auto bad:{Token::kQuestionPeriod,Token::kPeriod,Token::kTemplate}) {
   Parser p;p.scan.input={{Token::kQuestionPeriod,0},{bad,2},{Token::kName,4},{Token::kEos,5}};
   auto* result=p.Parse(p.storage.make());require(result==nullptr&&p.error&&p.ranges.empty()&&p.accept_depth==0);++checks;
  }
 }
 std::printf("PASS: %u optional-link range, chaining and syntax-path checks\n",checks);
}
''')
shutil.copy2(root/'deps/v8/LICENSE',out/'V8-LICENSE');shutil.copy2('work/node-wasm-grow-controls-20261007/run.py',out/'run.py')
print('Prepared exact optional-link parsing loop and source-range controls.')
