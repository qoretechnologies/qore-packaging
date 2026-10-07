// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
PreParserIdentifier PreParser::ParseIdentifier() {
  PreParserIdentifier result=PreParserIdentifier::Default();
  if(token==Token::kInvalid) {error=true;result.string_=&empty;}
  else {require(symbol);result.string_=symbol;}
  return result;
}
