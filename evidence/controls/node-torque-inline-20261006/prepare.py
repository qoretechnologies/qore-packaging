# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil,subprocess
root=Path.cwd();source=root/'work/node-obs-diagnostic-20261006/node-v24.18.1';out=root/'work/node-torque-inline-control-20261006';out.mkdir(exist_ok=True)
path='deps/v8/src/torque/implementation-visitor.cc';s=(source/path).read_text();a=s.index('  Block* macro_end;');b=s.index('\nvoid ImplementationVisitor::VisitMacroCommon',a);body=s[a:b];prefix='''VisitResult ImplementationVisitor::InlineMacro(Macro* macro) {
  const Type* return_type = macro->signature().return_type;
  bool can_return = return_type != TypeOracle::GetNeverType();
'''
(out/'source-extracts.json').write_text(json.dumps({'file':path,'line':s[:a].count('\n')+1,'body':body,'sha256':hashlib.sha256(body.encode()).hexdigest(),'return_guard':s[s.index('const Type* ImplementationVisitor::Visit(ReturnStatement* stmt)'):s.index('\nVisitResult ImplementationVisitor::Visit(TryLabelExpression* expr)')]},indent=2)+'\n')
header=r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Unchanged InlineMacro branch body; observable typed stack, AST and assembler adapters.
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>
void require(bool b) { if (!b) { std::abort(); } }
struct Type { int tag; bool IsNever() const { return tag==0; } bool IsVoid() const { return tag==1; } bool IsConstexpr() const { return tag==3; } bool IsTopType() const { return tag==4; } };
struct TopType:Type { const Type* src; const Type* source_type() const { return src; } static const TopType* cast(const Type* p) { require(p->IsTopType());return static_cast<const TopType*>(p); } };
struct TypeOracle { inline static Type never{0},void_type{1},value{2},constexpr_type{3};static const Type* GetNeverType() { return &never; } };
template<class T> struct Stack:std::vector<T> { void PushMany(const std::vector<T>& x) { this->insert(this->end(),x.begin(),x.end()); } size_t TopRange(size_t n) const { require(n<=this->size());return n; } };
std::vector<const Type*> LowerType(const Type* t) { if(t->IsVoid()||t->IsNever()||t->IsConstexpr()) { return {}; } return {t}; }
struct VisitResult { const Type* type=nullptr;size_t slots=0; VisitResult()=default;VisitResult(const Type* t,size_t s):type(t),slots(s) {} static VisitResult NeverResult() { return {TypeOracle::GetNeverType(),0}; } };
struct Block { Stack<const Type*> stack; };
struct LocalLabel { Block* block;std::vector<const Type*> types; };
struct LabelBindingsManager { static int& Get() { static int m;return m; } };
const char* kMacroEndLabelName="macro_end";
template<class T> struct Binding { T value; Binding(int*,const char*,T v):value(std::move(v)) {} };
struct Signature { const Type* return_type; };
struct Body { const Type* result; unsigned returns; };
struct Macro { Signature sig; Body body_; unsigned returns_=0; const Signature& signature() const { return sig; } const Body* body() const { return &body_; } bool HasReturns() const { return returns_!=0; } void IncrementReturns() { ++returns_; } const char* ReadableName() const { return "control"; } };
[[noreturn]] void ReportError(const std::string& s) { throw std::runtime_error(s); }
struct Assembler { Stack<const Type*> stack;std::unique_ptr<Block> block;unsigned gotos=0,binds=0;Stack<const Type*> CurrentStack() const { return stack; } Block* NewBlock(Stack<const Type*> s) { for(auto* t:s) { require(!t->IsTopType()); } block=std::make_unique<Block>(Block{std::move(s)});return block.get(); } void Goto(Block* p) { require(p==block.get() && p);++gotos; } void Bind(Block* p) { require(p==block.get() && p);++binds; } };
struct ImplementationVisitor {
 Assembler a;VisitResult result;Macro* active;
 Assembler& assembler() { return a; }
 void SetReturnValue(VisitResult v) { result=v; }
 VisitResult GetAndClearReturnValue() { return std::exchange(result,VisitResult{}); }
 const Type* Visit(const Body& b) {
  for(unsigned i=0;i<b.returns;++i) {
   // Mirrors Visit(ReturnStatement)'s precondition before IncrementReturns.
   if(active->signature().return_type->IsNever()) { ReportError("cannot return from a function with return type never"); }
   active->IncrementReturns();
  }
  return b.result;
 }
 __attribute__((noinline)) VisitResult InlineMacro(Macro* macro);
};
'''
test=r'''
int main() {
 unsigned cases=0,errors=0;
 for(unsigned repeat=0;repeat<10000;++repeat) {
  for(const Type* declared:{&TypeOracle::never,&TypeOracle::void_type,&TypeOracle::value,&TypeOracle::constexpr_type}) {
   for(const Type* result:{&TypeOracle::never,&TypeOracle::void_type}) {
    for(unsigned returns:{0u,1u,3u}) {
     for(bool top:{false,true}) {
      Macro m{{declared},{result,returns}};ImplementationVisitor v;v.active=&m;
      TopType wrapped{{4},&TypeOracle::value};v.a.stack.push_back(top ? static_cast<const Type*>(&wrapped) : &TypeOracle::value);
      bool bad=(declared->IsNever() && (returns || !result->IsNever())) || (!declared->IsNever() && result->IsNever() && !returns) || (!result->IsNever() && !declared->IsVoid());
      bool rejected=false;
      try { v.InlineMacro(&m); } catch(const std::runtime_error&) { rejected=true;++errors; }
      require(rejected==bad);
      require(bool(v.a.block)==!declared->IsNever());
      if(!bad) {
       require(v.a.gotos==unsigned(!result->IsNever()));
       require(v.a.binds==unsigned(returns || !result->IsNever()));
       require(m.returns_==returns);
       if(v.a.block) { require(v.a.block->stack[0]==&TypeOracle::value); }
      }
      ++cases;
     }
    }
   }
  }
 }
 std::printf("%u macro flow cases pass (%u expected semantic rejections)\n",cases,errors);
}
'''
(out/'control.cc').write_text(header+prefix+body+test);shutil.copy2(source/'deps/v8/LICENSE',out/'V8-LICENSE')
run=Path('work/node-torque-debug-control-20261006/run.py').read_text();(out/'run.py').write_text(run)
image='sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414'
cmd=['docker','run','--rm','--init','--network','none','--user','1019:100','-v',str(out)+':/work',image,'python3','-B','-W','error','/work/run.py'];(out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (out/'run.log').open('x') as log: subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
print('Torque macro flow release/debug controls complete')
