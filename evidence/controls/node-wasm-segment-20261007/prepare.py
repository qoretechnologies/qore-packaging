# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil
root=Path('work/node-obs-diagnostic-20261006/node-v24.18.1');out=Path('work/node-wasm-segment-controls-20261007');extracts=[]
def take(path,start,end):
 s=(root/path).read_text();a=s.index(start);body=s[a:s.index(end,a)].rstrip();extracts.append(dict(file=path,line=s[:a].count('\n')+1,body=body,sha256=hashlib.sha256(body.encode()).hexdigest()));return body
ops='deps/v8/src/compiler/turboshaft/operations.h';matcher='deps/v8/src/compiler/turboshaft/operation-matcher.h';graph='deps/v8/src/wasm/turboshaft-graph-interface.cc'
kind=take(ops,'  enum class Kind : uint8_t {\n    kWord32,','\n\n')
integral=take(ops,'  uint64_t integral() const {','\n  uint32_t word32()')
predicate=take(ops,'  bool IsIntegral() const {','\n\n  auto options()')
match=take(matcher,'  bool MatchIntegralWordConstant(V<Any> matched, WordRepresentation rep,','\n  bool MatchIntegralWord32Constant(V<Any> matched, uint32_t*')
match32=take(matcher,'  bool MatchIntegralWord32Constant(V<Any> matched, int32_t*','\n  template <typename T = intptr_t>')
stub=take(matcher,'  bool MatchWasmStubCallConstant(','\n  template <typename T>\n  bool MatchChange(')
recognize=take(graph,'  const CallOp* IsArrayNewSegment(','\n  V<HeapObject> StringNewWtf8ArrayImpl(')
scalar=take(graph,'      OpIndex segment_index = array_new->input(1);','\n      // Arbitrary choice for the second tagged parameter:')
source=r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <optional>
#include <vector>
void require(bool b) {if(!b) {std::abort();}}
#ifdef DEBUG
#define DCHECK(x) require(x)
#define DCHECK_IMPLIES(a,b) require(!(a)||(b))
#define DCHECK_LT(a,b) require((a)<(b))
#else
#define DCHECK(x) ((void)0)
#define DCHECK_IMPLIES(a,b) ((void)0)
#define DCHECK_LT(a,b) ((void)0)
#endif
#define UNREACHABLE() std::abort()
struct OpIndex {int id=-1;bool valid() const {return id>=0;}};
struct Any {};struct Object {};
template<class T> using V=OpIndex;
struct Operation {
 virtual ~Operation()=default;
 template<class T> const T* TryCast() const {return dynamic_cast<const T*>(this);}
};
struct ConstantOp:Operation {
'''+kind+r'''
 Kind kind;struct Storage {uint64_t integral;} storage;
 ConstantOp(Kind k,uint64_t value):kind(k),storage{value} {}
'''+predicate+'\n'+integral+r'''
};
struct CallOp:Operation {
 std::vector<OpIndex> inputs;
 explicit CallOp(std::vector<OpIndex> values):inputs(std::move(values)) {}
 OpIndex callee() const {return inputs.at(0);}
 OpIndex input(unsigned index) const {return inputs.at(index);}
};
struct WasmTypeAnnotationOp:Operation {
 OpIndex target;explicit WasmTypeAnnotationOp(OpIndex value):target(value) {}
 OpIndex value() const {return target;}
};
struct DidntThrowOp:Operation {
 OpIndex target;explicit DidntThrowOp(OpIndex value):target(value) {}
 OpIndex throwing_operation() const {return target;}
};
struct Graph {
 std::vector<std::unique_ptr<Operation>> nodes;
 const Operation& Get(OpIndex index) const {require(index.valid());return *nodes.at(index.id);}
 template<class T,class... Args> OpIndex Add(Args&&... args) {
  nodes.push_back(std::make_unique<T>(std::forward<Args>(args)...));return {static_cast<int>(nodes.size()-1)};
 }
};
struct WordRepresentation {
 enum Kind {K32,K64};Kind kind;
 WordRepresentation(Kind k):kind(k) {}
 Kind value() const {return kind;}
 static Kind Word32() {return K32;}
 static Kind Word64() {return K64;}
};
struct OperationMatcher {
 const Graph& graph;
 explicit OperationMatcher(const Graph& value):graph(value) {}
 template<class T> const T* TryCast(OpIndex index) const {return graph.Get(index).template TryCast<T>();}
'''+match+'\n'+match32+'\n'+stub+r'''
};
enum class Builtin:uint64_t {kWasmArrayNewSegment=1,kOther=2,kFirstBytecodeHandler=3};
struct Smi {
 int32_t value;
 static Smi FromInt(int32_t value) {require(value>=-(1<<30) && value<(1<<30));return {value};}
};
#define __ this->
struct Builder {
 Graph graph;bool unreachable=false;
 bool generating_unreachable_operations() const {return unreachable;}
 const Graph& output_graph() const {return graph;}
 OpIndex SmiConstant(Smi value) {return graph.Add<ConstantOp>(ConstantOp::Kind::kSmi,static_cast<uint64_t>(int64_t(value.value)));}
'''+recognize+r'''
 __attribute__((noinline)) std::optional<int32_t> Shortcut(V<Object> array) {
  if(const CallOp* array_new=IsArrayNewSegment(array)) {
'''+scalar+r'''
   return static_cast<int32_t>(graph.Get(index_smi).TryCast<ConstantOp>()->storage.integral);
  }
  return std::nullopt;
 }
};
int main() {
 using K=ConstantOp::Kind;unsigned checks=0;
 for(unsigned repeat=0;repeat<100;++repeat) {
  for(uint32_t index:{0u,1u,127u,128u,255u,256u,65535u,99999u}) {
   for(unsigned wrappers=0;wrappers<4;++wrappers) {
    for(unsigned target=0;target<4;++target) {for(bool unreachable:{false,true}) {
     Builder builder;builder.unreachable=unreachable;
     auto callee=target==2?builder.graph.Add<Operation>():builder.graph.Add<ConstantOp>(K::kRelocatableWasmStubCall,target==1?2:1);
     // This is the producer's Word32Constant(segment_imm.index) contract.
     auto segment=builder.graph.Add<ConstantOp>(K::kWord32,index);
     OpIndex node=target==3?segment:builder.graph.Add<CallOp>(std::vector<OpIndex>{callee,segment});
     if(wrappers&2) {node=builder.graph.Add<DidntThrowOp>(node);}
     if(wrappers&1) {node=builder.graph.Add<WasmTypeAnnotationOp>(node);}
     auto result=builder.Shortcut(node);
     if(target==0 && !unreachable) {require(result && *result==static_cast<int32_t>(index));}
     else {require(!result);}
     ++checks;
    }}
   }
  }
  Builder unreachable;unreachable.unreachable=true;require(!unreachable.Shortcut(OpIndex{}));++checks;
  // Rejected nonintegral inputs must not alter the matcher's output.
  for(K kind:{K::kFloat32,K::kFloat64,K::kSmi,K::kNumber,K::kExternal,K::kHeapObject}) {
   Builder b;auto node=b.graph.Add<ConstantOp>(kind,42);int32_t value=-177;
   require(!OperationMatcher(b.graph).MatchIntegralWord32Constant(node,&value) && value==-177);++checks;
  }
 }
 std::printf("PASS: %u Wasm segment producer, wrapper and matcher checks\n",checks);
}
'''
(out/'control.cc').write_text(source);(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n');shutil.copy2(root/'deps/v8/LICENSE',out/'V8-LICENSE')
s=Path('work/node-lookaround-controls-20261007/run.py').read_text();(out/'run.py').write_text(s)
print('Prepared exact recognizer, scalar shortcut and integer matcher bodies.')
