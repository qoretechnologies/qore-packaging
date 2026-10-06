# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil,subprocess
root=Path.cwd();src=root/'work/node-obs-diagnostic-20261006/node-v24.18.1';out=root/'work/node-conversion-enum-controls-20261006';out.mkdir();extracts=[]
def take(path,start,end):
 s=(src/path).read_text();a=s.index(start);b=s.index(end,a);body=s[a:b].rstrip();extracts.append({'file':path,'line':s[:a].count('\n')+1,'body':body,'sha256':hashlib.sha256(body.encode()).hexdigest()});return body
machine=take('deps/v8/src/codegen/machine-type.h','enum class MachineRepresentation','\nbool IsSubtype')
pointer=take('deps/v8/src/codegen/machine-type.h','constexpr inline bool CanBeTaggedPointer','\nconstexpr inline bool CanBeTaggedSigned')
barriers=take('deps/v8/src/compiler/write-barrier-kind.h','enum WriteBarrierKind','\ninline size_t hash_value')
store=take('deps/v8/src/compiler/code-assembler.h','enum class StoreToObjectWriteBarrier','\n\n')
mode=take('deps/v8/src/compiler/simplified-operator.h','enum class CheckTaggedInputMode','\n\n')
maglev=take('deps/v8/src/maglev/maglev-ir.h','enum class TaggedToFloat64ConversionType','\n\n')
s=(src/'deps/v8/src/compiler/turboshaft/operations.h').read_text();a=s.index('struct ConvertJSPrimitiveToUntaggedOrDeoptOp');a=s.index('  enum class JSPrimitiveKind',a);b=s.index(';',s.index('}',a))+1;primitive=s[a:b];extracts.append({'file':'deps/v8/src/compiler/turboshaft/operations.h','line':s[:a].count('\n')+1,'body':primitive,'sha256':hashlib.sha256(primitive.encode()).hexdigest()})
store_body=take('deps/v8/src/compiler/code-assembler.cc','void CodeAssembler::StoreToObject(','\nvoid CodeAssembler::OptimizedStoreField')
truncate=take('deps/v8/src/compiler/turboshaft/graph-builder.cc','      using IR = TruncateJSPrimitiveToUntaggedOrDeoptOp::InputRequirement;','\n      return __ TruncateJSPrimitiveToUntaggedOrDeopt(')
convert=take('deps/v8/src/compiler/turboshaft/graph-builder.cc','      ConvertJSPrimitiveToUntaggedOrDeoptOp::JSPrimitiveKind from_kind;','\n      return __ ConvertJSPrimitiveToUntaggedOrDeopt(')
maglev_body=take('deps/v8/src/compiler/turboshaft/turbolev-graph-builder.cc','    TruncateJSPrimitiveToUntaggedOrDeoptOp::InputRequirement input_requirement;','\n    GET_FRAME_STATE_MAYBE_ABORT')
header='''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Original enum declarations, pointer predicate, store method and conversion switches.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
void require(bool b) { if (!b) { std::abort(); } }
'''+machine+'\n'+pointer+'\n'+barriers+'\n'+store+'\n'+mode+'\nnamespace maglev {\n'+maglev+'\n}\nstruct ConvertJSPrimitiveToUntaggedOrDeoptOp {\n'+primitive+'\n};\nstruct TruncateJSPrimitiveToUntaggedOrDeoptOp { using InputRequirement=ConvertJSPrimitiveToUntaggedOrDeoptOp::JSPrimitiveKind; };\n'
header+='''
using IR=TruncateJSPrimitiveToUntaggedOrDeoptOp::InputRequirement;
struct Params { CheckTaggedInputMode value; CheckTaggedInputMode mode() const { return value; } };
struct GraphNode { Params params; const Params& op() const { return params; } };
const Params& CheckTaggedInputParametersOf(const Params& p) { return p; }
struct MaglevNode { maglev::TaggedToFloat64ConversionType mode; auto conversion_type() const { return mode; } };
struct Node { int id; };
struct Object {};
struct IntPtrT {};
template<class T> using TNode=Node*;
struct RawAssembler {
 MachineRepresentation rep; Node *object=nullptr,*offset=nullptr,*value=nullptr; WriteBarrierKind barrier; unsigned calls=0;
 void StoreToObject(MachineRepresentation r,Node* o,Node* off,Node* v,WriteBarrierKind b) { rep=r;object=o;offset=off;value=v;barrier=b;++calls; }
};
struct CodeAssembler { RawAssembler raw; RawAssembler* raw_assembler() { return &raw; }
 __attribute__((noinline)) void StoreToObject(MachineRepresentation rep,TNode<Object> object,TNode<IntPtrT> offset,Node* value,StoreToObjectWriteBarrier write_barrier);
};
'''
functions=store_body+'\n__attribute__((noinline)) IR Truncate(GraphNode* node) {\n'+truncate+'\nreturn input_requirement;\n}\n__attribute__((noinline)) IR Convert(const Params& params) {\n'+convert+'\nreturn from_kind;\n}\n__attribute__((noinline)) IR MaglevTruncate(MaglevNode* node) {\n'+maglev_body+'\nreturn input_requirement;\n}\n'
tests=r'''
int main() {
 const std::array<CheckTaggedInputMode,4> modes{CheckTaggedInputMode::kAdditiveSafeInteger,CheckTaggedInputMode::kNumber,CheckTaggedInputMode::kNumberOrBoolean,CheckTaggedInputMode::kNumberOrOddball};
 const std::array<IR,4> mapped{IR::kAdditiveSafeInteger,IR::kNumber,IR::kNumberOrBoolean,IR::kNumberOrOddball};
 const std::array<maglev::TaggedToFloat64ConversionType,3> maglev_modes{maglev::TaggedToFloat64ConversionType::kOnlyNumber,maglev::TaggedToFloat64ConversionType::kNumberOrBoolean,maglev::TaggedToFloat64ConversionType::kNumberOrOddball};
 Node nodes[4]{{11},{22},{33},{44}};unsigned checks=0;
 for(unsigned repeat=0;repeat<10000;++repeat) {
  for(size_t i=0;i<modes.size();++i) { GraphNode node{{modes[i]}};require(Truncate(&node)==mapped[i]);require(Convert(node.params)==mapped[i]);checks+=2; }
  for(size_t i=0;i<maglev_modes.size();++i) { MaglevNode node{maglev_modes[i]};require(MaglevTruncate(&node)==mapped[i+1]);++checks; }
  for(unsigned v=0;v<=static_cast<unsigned>(MachineRepresentation::kLastRepresentation);++v) {
   auto rep=static_cast<MachineRepresentation>(v);
   for(auto barrier:{StoreToObjectWriteBarrier::kNone,StoreToObjectWriteBarrier::kMap,StoreToObjectWriteBarrier::kFull}) {
    for(unsigned n=0;n<4;++n) {
     CodeAssembler assembler;Node *object=&nodes[n],*offset=&nodes[(n+1)%4],*value=&nodes[(n+2)%4];assembler.StoreToObject(rep,object,offset,value,barrier);
     WriteBarrierKind expected=kFullWriteBarrier;
     if(barrier==StoreToObjectWriteBarrier::kMap) { expected=kMapWriteBarrier; }
     if(barrier==StoreToObjectWriteBarrier::kNone) {
      expected=(rep==MachineRepresentation::kMapWord||rep==MachineRepresentation::kTagged||rep==MachineRepresentation::kTaggedPointer) ? kAssertNoWriteBarrier : kNoWriteBarrier;
     }
     require(assembler.raw.barrier==expected && assembler.raw.calls==1 && assembler.raw.rep==rep && assembler.raw.object==object && assembler.raw.offset==offset && assembler.raw.value==value);++checks;
    }
   }
  }
 }
 std::printf("PASS: %u conversion and store dispatch checks across all declared input enum values\n",checks);
}
'''
(out/'control.cc').write_text(header+functions+tests);(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n');shutil.copy2(src/'deps/v8/LICENSE',out/'V8-LICENSE');shutil.copy2(root/'work/node-torque-debug-control-20261006/run.py',out/'run.py')
cmd=['docker','run','--rm','--init','--network','none','--user','1019:100','-v',str(out)+':/work','sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414','python3','-B','-W','error','/work/run.py'];(out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (out/'run.log').open('x') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
