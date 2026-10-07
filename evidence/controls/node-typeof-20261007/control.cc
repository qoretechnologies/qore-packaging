// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Verbatim typeof dispatch with a typed, owned predicate-graph evaluator.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <vector>
void require(bool condition) {if(!condition) {std::abort();}}
struct Rejected {};
[[noreturn]] void unreachable() {throw Rejected{};}
#define UNREACHABLE() unreachable()
#define TYPEOF_LITERAL_LIST(V) \
  V(Number, number)            \
  V(String, string)            \
  V(Symbol, symbol)            \
  V(Boolean, boolean)          \
  V(BigInt, bigint)            \
  V(Undefined, undefined)      \
  V(Function, function)        \
  V(Object, object)            \
  V(Other, other)
namespace interpreter {struct TestTypeOfFlags {
  enum class LiteralFlag : uint8_t {
#define DECLARE_LITERAL_FLAG(name, _) k##name,
    TYPEOF_LITERAL_LIST(DECLARE_LITERAL_FLAG)
#undef DECLARE_LITERAL_FLAG
  };
};}
enum class MachineRepresentation {kTagged};
enum class ValueType {Number,String,Symbol,BigInt,Boolean,Undefined,Function,Object,Null};
struct Node {ValueType type;bool boolean=false;};
enum class Predicate {Number,String,Symbol,BigInt,Equal,Select,Undetectable,Function,NonCallable};
struct Operators {
 Predicate ObjectIsNumber() const {return Predicate::Number;}
 Predicate ObjectIsString() const {return Predicate::String;}
 Predicate ObjectIsSymbol() const {return Predicate::Symbol;}
 Predicate ObjectIsBigInt() const {return Predicate::BigInt;}
 Predicate ReferenceEqual() const {return Predicate::Equal;}
 Predicate Select(MachineRepresentation) const {return Predicate::Select;}
 Predicate ObjectIsUndetectable() const {return Predicate::Undetectable;}
 Predicate ObjectIsDetectableCallable() const {return Predicate::Function;}
 Predicate ObjectIsNonCallable() const {return Predicate::NonCallable;}
};
struct Builder {
 Operators ops;
 Node true_{ValueType::Boolean,true},false_{ValueType::Boolean,false},null_{ValueType::Null};
 std::vector<std::unique_ptr<Node>> owned;
 Operators* simplified() {return &ops;}
 Operators* common() {return &ops;}
 Builder* graph() {return this;}
 Builder* jsgraph() {return this;}
 Node* TrueConstant() {return &true_;}
 Node* FalseConstant() {return &false_;}
 Node* NullConstant() {return &null_;}
 Node* NewNode(Predicate predicate, Node* a, Node* b=nullptr, Node* c=nullptr) {
  bool result=false;
  switch(predicate) {
   case Predicate::Number:result=a->type==ValueType::Number;break;
   case Predicate::String:result=a->type==ValueType::String;break;
   case Predicate::Symbol:result=a->type==ValueType::Symbol;break;
   case Predicate::BigInt:result=a->type==ValueType::BigInt;break;
   case Predicate::Equal:require(b);result=a==b;break;
   case Predicate::Select:require(a->type==ValueType::Boolean&&b&&c);return a->boolean?b:c;
   case Predicate::Undetectable:result=a->type==ValueType::Undefined;break;
   case Predicate::Function:result=a->type==ValueType::Function;break;
   case Predicate::NonCallable:result=a->type==ValueType::Object;break;
  }
  auto node=std::make_unique<Node>(Node{ValueType::Boolean,result});auto* ptr=node.get();owned.push_back(std::move(node));return ptr;
 }
 __attribute__((noinline)) Node* choose(Node* object, interpreter::TestTypeOfFlags::LiteralFlag literal_flag) {
  Node* result;
  switch (literal_flag) {
    case interpreter::TestTypeOfFlags::LiteralFlag::kNumber:
      result = NewNode(simplified()->ObjectIsNumber(), object);
      break;
    case interpreter::TestTypeOfFlags::LiteralFlag::kString:
      result = NewNode(simplified()->ObjectIsString(), object);
      break;
    case interpreter::TestTypeOfFlags::LiteralFlag::kSymbol:
      result = NewNode(simplified()->ObjectIsSymbol(), object);
      break;
    case interpreter::TestTypeOfFlags::LiteralFlag::kBigInt:
      result = NewNode(simplified()->ObjectIsBigInt(), object);
      break;
    case interpreter::TestTypeOfFlags::LiteralFlag::kBoolean:
      result = NewNode(common()->Select(MachineRepresentation::kTagged),
                       NewNode(simplified()->ReferenceEqual(), object,
                               jsgraph()->TrueConstant()),
                       jsgraph()->TrueConstant(),
                       NewNode(simplified()->ReferenceEqual(), object,
                               jsgraph()->FalseConstant()));
      break;
    case interpreter::TestTypeOfFlags::LiteralFlag::kUndefined:
      result = graph()->NewNode(
          common()->Select(MachineRepresentation::kTagged),
          graph()->NewNode(simplified()->ReferenceEqual(), object,
                           jsgraph()->NullConstant()),
          jsgraph()->FalseConstant(),
          graph()->NewNode(simplified()->ObjectIsUndetectable(), object));
      break;
    case interpreter::TestTypeOfFlags::LiteralFlag::kFunction:
      result =
          graph()->NewNode(simplified()->ObjectIsDetectableCallable(), object);
      break;
    case interpreter::TestTypeOfFlags::LiteralFlag::kObject:
      result = graph()->NewNode(
          common()->Select(MachineRepresentation::kTagged),
          graph()->NewNode(simplified()->ObjectIsNonCallable(), object),
          jsgraph()->TrueConstant(),
          graph()->NewNode(simplified()->ReferenceEqual(), object,
                           jsgraph()->NullConstant()));
      break;
    case interpreter::TestTypeOfFlags::LiteralFlag::kOther:
      UNREACHABLE();  // Should never be emitted.
  }
 return result;
 }
};
int main() {
 using L=interpreter::TestTypeOfFlags::LiteralFlag;
 const std::array flags{L::kNumber,L::kString,L::kSymbol,L::kBigInt,L::kBoolean,L::kUndefined,L::kFunction,L::kObject};
 unsigned checks=0;
 for(unsigned repeat=0;repeat<10000;++repeat) {
  Builder builder;
  std::array values{Node{ValueType::Number},Node{ValueType::String},Node{ValueType::Symbol},Node{ValueType::BigInt},
                    Node{ValueType::Undefined},Node{ValueType::Function},Node{ValueType::Object}};
  for(unsigned flag=0;flag<flags.size();++flag) {
   for(auto& input:values) {
    auto* result=builder.choose(&input,flags[flag]);require(result->type==ValueType::Boolean);
    unsigned expected=static_cast<unsigned>(input.type);
    require(result->boolean==(flag==expected));++checks;
   }
   for(auto* input:{builder.TrueConstant(),builder.FalseConstant(),builder.NullConstant()}) {
    auto* result=builder.choose(input,flags[flag]);require(result->type==ValueType::Boolean);
    require(result->boolean==(flag==(input->type==ValueType::Null?7u:4u)));++checks;
   }
  }
  size_t old_size=builder.owned.size();bool rejected=false;
  try {builder.choose(builder.NullConstant(),L::kOther);} catch(const Rejected&) {rejected=true;}
  require(rejected);require(builder.owned.size()==old_size);++checks;
 }
 std::printf("PASS: %u typeof dispatch and rejection checks\n",checks);
}
