# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib
import json
import shutil

root = Path('work/node-obs-diagnostic-20261006/node-v24.18.1')
out = Path('work/node-typeof-controls-20261007')
out.mkdir()
extracts = []

def take(path, begin, end):
    source = (root / path).read_text()
    start = source.index(begin)
    body = source[start:source.index(end, start)].rstrip()
    extracts.append(dict(file=path, line=source[:start].count('\n') + 1, body=body,
                         sha256=hashlib.sha256(body.encode()).hexdigest()))
    return body

header = 'deps/v8/src/interpreter/bytecode-flags-and-tokens.h'
macro = take(header, '#define TYPEOF_LITERAL_LIST', '\nclass TestTypeOfFlags')
enum = take(header, '  enum class LiteralFlag', '\n\n  static LiteralFlag GetFlagForLiteral')
body = take('deps/v8/src/compiler/bytecode-graph-builder.cc', '  Node* result;\n  switch (literal_flag)',
            '\n  environment()->BindAccumulator(result);')
source = r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
'''+macro+r'''
namespace interpreter {struct TestTypeOfFlags {
'''+enum+r'''
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
'''+body+r'''
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
'''
(out / 'control.cc').write_text(source)
(out / 'source-extracts.json').write_text(json.dumps(extracts, indent=2) + '\n')
shutil.copy2(root / 'deps/v8/LICENSE', out / 'V8-LICENSE')
shutil.copy2('work/node-object-dispatch-controls-20261007/run.py', out / 'run.py')
