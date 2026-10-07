// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
