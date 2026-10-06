// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// V8's unchanged visitor and instruction; minimal observable AST/type/assembler adapters.
#include <cstdio>
#include <cstdlib>
#include <string>
#include <utility>
#define TORQUE_INSTRUCTION_BOILERPLATE()
#define UNREACHABLE() std::abort()
struct InstructionBase {
 virtual bool IsBlockTerminator() const = 0;
 virtual ~InstructionBase() = default;
};
namespace base { constexpr const char* kUnreachableCodeMessage = "unreachable code"; }
struct AbortInstruction : InstructionBase {
  TORQUE_INSTRUCTION_BOILERPLATE()
  enum class Kind { kDebugBreak, kUnreachable, kAssertionFailure };
  bool IsBlockTerminator() const override { return kind != Kind::kDebugBreak; }
  explicit AbortInstruction(Kind kind, std::string message = "")
      : kind(kind), message(std::move(message)) {}
  static const char* KindToString(Kind kind) {
    switch (kind) {
      case Kind::kDebugBreak:
        return "kDebugBreak";
      case Kind::kUnreachable:
        return "kUnreachable";
      case Kind::kAssertionFailure:
        return "kAssertionFailure";
    }
    UNREACHABLE();
  }

  Kind kind;
  std::string message;
};

struct Type { int tag; };
struct TypeOracle {
 inline static Type never{1}, void_type{2};
 static const Type* GetNeverType() { return &never; }
 static const Type* GetVoidType() { return &void_type; }
};
struct DebugStatement {
 enum class Kind { kUnreachable, kDebug };
 Kind kind;
 std::string pos;
};
std::string PositionAsString(const std::string& pos) { return pos; }
struct PrintErrorInstruction { std::string message; };
struct Assembler {
 unsigned aborts=0, prints=0;
 AbortInstruction::Kind kind=AbortInstruction::Kind::kAssertionFailure;
 std::string error, message;
 bool terminator=false;
 void Emit(const AbortInstruction& instruction) {
  ++aborts; kind=instruction.kind; message=instruction.message;
  terminator=instruction.IsBlockTerminator();
 }
 void Emit(const PrintErrorInstruction& instruction) { ++prints;error=instruction.message; }
};
struct ImplementationVisitor {
 Assembler a;
 Assembler& assembler() { return a; }
 __attribute__((noinline)) const Type* Visit(DebugStatement*);
};
const Type* ImplementationVisitor::Visit(DebugStatement* stmt) {
  std::string reason;
  const Type* return_type;
  AbortInstruction::Kind kind;
  switch (stmt->kind) {
    case DebugStatement::Kind::kUnreachable:
      // Use the same string as in C++ to simplify fuzzer pattern-matching.
      reason = base::kUnreachableCodeMessage;
      return_type = TypeOracle::GetNeverType();
      kind = AbortInstruction::Kind::kUnreachable;
      break;
    case DebugStatement::Kind::kDebug:
      reason = "debug break";
      return_type = TypeOracle::GetVoidType();
      kind = AbortInstruction::Kind::kDebugBreak;
      break;
  }
#if defined(DEBUG)
  assembler().Emit(PrintErrorInstruction{"halting because of " + reason +
                                         " at " + PositionAsString(stmt->pos)});
#endif
  assembler().Emit(AbortInstruction{kind});
  return return_type;
}

void require(bool value) { if (!value) { std::abort(); } }
int main() {
 unsigned cases=0;
 for (unsigned iteration=0; iteration<100000; ++iteration) {
  for (auto kind: {DebugStatement::Kind::kUnreachable, DebugStatement::Kind::kDebug}) {
   DebugStatement stmt{kind, iteration%2 ? "fixture.tq:17:4" : ""};
   ImplementationVisitor visitor;
   const Type* result=visitor.Visit(&stmt);
   bool unreachable=kind==DebugStatement::Kind::kUnreachable;
   require(result==(unreachable ? TypeOracle::GetNeverType() : TypeOracle::GetVoidType()));
   require(visitor.a.aborts==1);
   require(visitor.a.kind==(unreachable ? AbortInstruction::Kind::kUnreachable : AbortInstruction::Kind::kDebugBreak));
   require(visitor.a.message.empty());
   require(visitor.a.terminator==unreachable);
#ifdef DEBUG
   require(visitor.a.prints==1);
   require(visitor.a.error==std::string("halting because of ")+(unreachable ? base::kUnreachableCodeMessage : "debug break")+" at "+stmt.pos);
#else
   require(visitor.a.prints==0);
   require(visitor.a.error.empty());
#endif
   ++cases;
  }
 }
 std::printf("%u exhaustive debug-statement cases passed\n",cases);
}
