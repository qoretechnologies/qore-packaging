// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
Expression* Parser::Parse(ExpressionT result) {
  bool optional_chaining = false;
  bool is_optional = false;
  int optional_link_begin;
  do {
    switch (peek()) {
      case Token::kQuestionPeriod: {
        if (is_optional) {
          ReportUnexpectedToken(peek());
          return impl()->FailureExpression();
        }
        // Include the ?. in the source range position.
        optional_link_begin = scanner()->peek_location().beg_pos;
        Consume(Token::kQuestionPeriod);
        is_optional = true;
        optional_chaining = true;
        if (Token::IsPropertyOrCall(peek())) continue;
        int pos = position();
        ExpressionT key = ParsePropertyOrPrivatePropertyName();
        result = factory()->NewProperty(result, key, pos, is_optional);
        break;
      }

      /* Property */
      case Token::kLeftBracket: {
        Consume(Token::kLeftBracket);
        int pos = position();
        AcceptINScope scope(this, true);
        ExpressionT index = ParseExpressionCoverGrammar();
        result = factory()->NewProperty(result, index, pos, is_optional);
        Expect(Token::kRightBracket);
        break;
      }

      /* Property */
      case Token::kPeriod: {
        if (is_optional) {
          ReportUnexpectedToken(Next());
          return impl()->FailureExpression();
        }
        Consume(Token::kPeriod);
        int pos = position();
        ExpressionT key = ParsePropertyOrPrivatePropertyName();
        result = factory()->NewProperty(result, key, pos, is_optional);
        break;
      }

      /* Call */
      case Token::kLeftParen: {
        int pos;
        if (Token::IsCallable(scanner()->current_token())) {
          // For call of an identifier we want to report position of
          // the identifier as position of the call in the stack trace.
          pos = position();
        } else {
          // For other kinds of calls we record position of the parenthesis as
          // position of the call. Note that this is extremely important for
          // expressions of the form function(){...}() for which call position
          // should not point to the closing brace otherwise it will intersect
          // with positions recorded for function literal and confuse debugger.
          pos = peek_position();
          // Also the trailing parenthesis are a hint that the function will
          // be called immediately. If we happen to have parsed a preceding
          // function literal eagerly, we can also compile it eagerly.
          if (result->IsFunctionLiteral()) {
            result->AsFunctionLiteral()->SetShouldEagerCompile();
          }
        }
        bool has_spread;
        ExpressionListT args(pointer_buffer());
        ParseArguments(&args, &has_spread);

        // Keep track of eval() calls since they disable all local variable
        // optimizations.
        // The calls that need special treatment are the
        // direct eval calls. These calls are all of the form eval(...), with
        // no explicit receiver.
        // These calls are marked as potentially direct eval calls. Whether
        // they are actually direct calls to eval is determined at run time.
        int eval_scope_info_index = 0;
        if (CheckPossibleEvalCall(result, is_optional, scope())) {
          eval_scope_info_index = GetNextInfoId();
        }

        result = factory()->NewCall(result, args, pos, has_spread,
                                    eval_scope_info_index, is_optional);

        fni_.RemoveLastFunction();
        break;
      }

      default:
        // Template literals in/after an Optional Chain not supported:
        if (optional_chaining) {
          impl()->ReportMessageAt(scanner()->peek_location(),
                                  MessageTemplate::kOptionalChainingNoTemplate);
          return impl()->FailureExpression();
        }
        /* Tagged Template */
        DCHECK(Token::IsTemplate(peek()));
        result = ParseTemplateLiteral(result, position(), true);
        break;
    }
    if (is_optional) {
      SourceRange chain_link_range(optional_link_begin, end_position());
      impl()->RecordExpressionSourceRange(result, chain_link_range);
      is_optional = false;
    }
  } while (Token::IsPropertyOrCall(peek()));
  if (optional_chaining) return factory()->NewOptionalChain(result);
  return result;
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
