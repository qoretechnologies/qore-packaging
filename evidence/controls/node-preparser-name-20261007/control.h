// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
class PreParserIdentifier {
 public:
  PreParserIdentifier() : type_(kUnknownIdentifier) {}
  static PreParserIdentifier Default() {
    return PreParserIdentifier(kUnknownIdentifier);
  }
  static PreParserIdentifier Null() {
    return PreParserIdentifier(kNullIdentifier);
  }
  static PreParserIdentifier Eval() {
    return PreParserIdentifier(kEvalIdentifier);
  }
  static PreParserIdentifier Arguments() {
    return PreParserIdentifier(kArgumentsIdentifier);
  }
  static PreParserIdentifier Constructor() {
    return PreParserIdentifier(kConstructorIdentifier);
  }
  static PreParserIdentifier Async() {
    return PreParserIdentifier(kAsyncIdentifier);
  }
  static PreParserIdentifier PrivateName() {
    return PreParserIdentifier(kPrivateNameIdentifier);
  }
  bool IsNull() const { return type_ == kNullIdentifier; }
  bool IsEval() const { return type_ == kEvalIdentifier; }
  bool IsAsync() const { return type_ == kAsyncIdentifier; }
  bool IsArguments() const { return type_ == kArgumentsIdentifier; }
  bool IsEvalOrArguments() const {
    static_assert(kEvalIdentifier + 1 == kArgumentsIdentifier);
    return base::IsInRange(type_, kEvalIdentifier, kArgumentsIdentifier);
  }
  bool IsConstructor() const { return type_ == kConstructorIdentifier; }
  bool IsPrivateName() const { return type_ == kPrivateNameIdentifier; }

 private:
  enum Type : uint8_t {
    kNullIdentifier,
    kUnknownIdentifier,
    kEvalIdentifier,
    kArgumentsIdentifier,
    kConstructorIdentifier,
    kAsyncIdentifier,
    kPrivateNameIdentifier
  };

  explicit PreParserIdentifier(Type type) : string_(nullptr), type_(type) {}
  const AstRawString* string_;

  Type type_;
  friend class PreParserExpression;
  friend class PreParser;
};

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
template <typename Impl>
typename ParserBase<Impl>::StatementT
ParserBase<Impl>::ParseHoistableDeclaration(
    int pos, ParseFunctionFlags flags, ZonePtrList<const AstRawString>* names,
    bool default_export) {
  CheckStackOverflow();

  // FunctionDeclaration ::
  //   'function' Identifier '(' FormalParameters ')' '{' FunctionBody '}'
  //   'function' '(' FormalParameters ')' '{' FunctionBody '}'
  // GeneratorDeclaration ::
  //   'function' '*' Identifier '(' FormalParameters ')' '{' FunctionBody '}'
  //   'function' '*' '(' FormalParameters ')' '{' FunctionBody '}'
  //
  // The anonymous forms are allowed iff [default_export] is true.
  //
  // 'function' and '*' (if present) have been consumed by the caller.

  DCHECK_IMPLIES((flags & ParseFunctionFlag::kIsAsync) != 0,
                 (flags & ParseFunctionFlag::kIsGenerator) == 0);

  if ((flags & ParseFunctionFlag::kIsAsync) != 0 && Check(Token::kMul)) {
    // Async generator
    flags |= ParseFunctionFlag::kIsGenerator;
  }

  IdentifierT name;
  FunctionNameValidity name_validity;
  IdentifierT variable_name;
  if (peek() == Token::kLeftParen) {
    if (default_export) {
      impl()->GetDefaultStrings(&name, &variable_name);
      name_validity = kSkipFunctionNameCheck;
    } else {
      ReportMessage(MessageTemplate::kMissingFunctionName);
      return impl()->NullStatement();
    }
  } else {
    bool is_strict_reserved = Token::IsStrictReservedWord(peek());
    name = ParseIdentifier();
    name_validity = is_strict_reserved ? kFunctionNameIsStrictReserved
                                       : kFunctionNameValidityUnknown;
    variable_name = name;
  }

  FuncNameInferrerState fni_state(&fni_);
  impl()->PushEnclosingName(name);

  FunctionKind function_kind = FunctionKindFor(flags);

  FunctionLiteralT function = impl()->ParseFunctionLiteral(
      name, scanner()->location(), name_validity, function_kind, pos,
      FunctionSyntaxKind::kDeclaration, language_mode(), nullptr);

  // In ES6, a function behaves as a lexical binding, except in
  // a script scope, or the initial scope of eval or another function.
  VariableMode mode =
      (!scope()->is_declaration_scope() || scope()->is_module_scope())
          ? VariableMode::kLet
          : VariableMode::kVar;
  // Async functions don't undergo sloppy mode block scoped hoisting, and don't
  // allow duplicates in a block. Both are represented by the
  // sloppy_block_functions_. Don't add them to the map for async functions.
  // Generators are also supposed to be prohibited; currently doing this behind
  // a flag and UseCounting violations to assess web compatibility.
  VariableKind kind = is_sloppy(language_mode()) &&
                              !scope()->is_declaration_scope() &&
                              flags == ParseFunctionFlag::kIsNormal
                          ? SLOPPY_BLOCK_FUNCTION_VARIABLE
                          : NORMAL_VARIABLE;

  return impl()->DeclareFunction(variable_name, function, mode, kind, pos,
                                 end_position(), names);
}
