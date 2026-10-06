# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil,subprocess
root=Path.cwd();src=root/'work/node-obs-diagnostic-20261006/node-v24.18.1';out=root/'work/node-call-enum-controls-20261006';out.mkdir();extracts=[]
def take(path,start,end,after=None):
 s=(src/path).read_text();offset=s.index(after) if after else 0;a=s.index(start,offset);b=s.index(end,a);body=s[a:b].rstrip();extracts.append({'file':path,'line':s[:a].count('\n')+1,'body':body,'sha256':hashlib.sha256(body.encode()).hexdigest()});return body
def enum(path,start,after=None):return take(path,start,';',after)+';'
globals='deps/v8/src/common/globals.h';ops='deps/v8/src/compiler/turboshaft/operations.h';mag='deps/v8/src/maglev/maglev-ir.h';turbo='deps/v8/src/compiler/turboshaft/turbolev-graph-builder.cc'
stub=enum(globals,'enum class StubCallMode');typeof=enum(globals,'enum class TypeofMode')
call=enum('deps/v8/src/compiler/linkage.h','  enum Kind {','class V8_EXPORT_PRIVATE CallDescriptor')
wasm=enum('deps/v8/src/compiler/wasm-compiler-definitions.h','enum WasmCallKind')
comparison=enum(ops,'  enum class Kind : uint8_t {','struct ComparisonOp :')
target=enum(mag,'  enum class TargetType {','class Call :')
conversion=enum(mag,'enum class TaggedToFloat64ConversionType')
primitive=enum(ops,'  enum class JSPrimitiveKind','struct ConvertJSPrimitiveToUntaggedOrDeoptOp')
typer=take('deps/v8/src/compiler/turboshaft/typer.cc','    bool is_signed, is_less_than;','\n    Type l_refined;')
stub_body=take('deps/v8/src/compiler/linkage.cc','  CallDescriptor::Kind kind;\n  MachineType target_type;','\n  RegList allocatable_registers')
wasm_body=take('deps/v8/src/compiler/wasm-compiler-definitions.cc','  CallDescriptor::Kind descriptor_kind;','\n  CallDescriptor::Flags flags')
forward=take(turbo,'    Builtin builtin;','\n    V<Object> call =', 'maglev::ProcessResult Process(maglev::CallForwardVarargs*')
load=take(turbo,'    Builtin builtin;','\n    GENERATE_AND_MAP_BUILTIN_CALL', 'maglev::ProcessResult Process(maglev::LoadGlobal*')
convert=take(turbo,'    ConvertJSPrimitiveToUntaggedOrDeoptOp::JSPrimitiveKind kind;','\n    SetMap(node,','template <typename NumberToFloat64Op>')
header='''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Unchanged upstream enum declarations and dispatch bodies; typed output adapters.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <utility>
void require(bool b) { if (!b) { std::abort(); } }
'''+stub+'\n'+typeof+'\nstruct CallDescriptor {\n'+call+'\n};\n'+wasm+'\nstruct ComparisonOp {\n'+comparison+'\nKind kind;\n};\nnamespace maglev { struct Call {\n'+target+'\n};\n'+conversion+'\n}\nstruct ConvertJSPrimitiveToUntaggedOrDeoptOp {\n'+primitive+'\n};\n'
header+='''
struct MachineType { unsigned value; static MachineType AnyTagged() { return {11}; } static MachineType Pointer() { return {22}; } };
using Signature=uint64_t;
constexpr uint64_t kInvalidWasmSignatureHash=std::numeric_limits<uint64_t>::max();
namespace wasm { struct SignatureHasher { static inline unsigned calls=0; static uint64_t Hash(const Signature* sig) { ++calls; return *sig; } }; }
enum class Builtin { kCallFunctionForwardVarargs, kCallForwardVarargs, kLoadGlobalICInsideTypeof, kLoadGlobalIC };
struct ForwardNode { maglev::Call::TargetType mode; auto target_type() const { return mode; } };
struct GlobalNode { TypeofMode mode; auto typeof_mode() const { return mode; } };
struct ConversionNode { maglev::TaggedToFloat64ConversionType mode; auto conversion_type() const { return mode; } };
struct ComparisonOutput { bool called=false; bool is_signed=false; bool is_less_than=false; };
'''
functions='''__attribute__((noinline)) void Compare(const ComparisonOp* comparison, ComparisonOutput& output) {
'''+typer+'''
output = {true, is_signed, is_less_than};
}
__attribute__((noinline)) std::pair<CallDescriptor::Kind, MachineType> Stub(StubCallMode stub_mode) {
'''+stub_body+'''
return {kind,target_type};
}
#if V8_ENABLE_WEBASSEMBLY
__attribute__((noinline)) std::pair<CallDescriptor::Kind,uint64_t> Wasm(WasmCallKind call_kind, const Signature* fsig) {
'''+wasm_body+'''
return {descriptor_kind,signature_hash};
}
#endif
__attribute__((noinline)) Builtin Forward(ForwardNode* node) {
'''+forward+'''
return builtin;
}
__attribute__((noinline)) Builtin Global(GlobalNode* node) {
'''+load+'''
return builtin;
}
__attribute__((noinline)) auto Convert(ConversionNode* node) {
'''+convert+'''
return kind;
}
'''
tests=r'''
int main() {
 using C=ComparisonOp::Kind; using P=ConvertJSPrimitiveToUntaggedOrDeoptOp::JSPrimitiveKind; using M=maglev::TaggedToFloat64ConversionType;
 const std::array<C,5> comparisons{C::kEqual,C::kSignedLessThan,C::kSignedLessThanOrEqual,C::kUnsignedLessThan,C::kUnsignedLessThanOrEqual};
 const std::array<M,3> conversions{M::kOnlyNumber,M::kNumberOrBoolean,M::kNumberOrOddball};
 const std::array<P,3> primitives{P::kNumber,P::kNumberOrBoolean,P::kNumberOrOddball};
 unsigned checks=0;
 for(unsigned repeat=0;repeat<10000;++repeat) {
  for(unsigned i=0;i<comparisons.size();++i) {
   ComparisonOp op{comparisons[i]};ComparisonOutput output{false,true,false};Compare(&op,output);
   if(i==0) { require(!output.called && output.is_signed && !output.is_less_than); }
   else { require(output.called && output.is_signed==(i<3) && output.is_less_than==(i==1||i==3)); }
   ++checks;
  }
  for(auto mode:{StubCallMode::kCallCodeObject,StubCallMode::kCallBuiltinPointer}) {
   auto [kind,type]=Stub(mode);require(type.value==11 && kind==(mode==StubCallMode::kCallCodeObject?CallDescriptor::kCallCodeObject:CallDescriptor::kCallBuiltinPointer));++checks;
  }
#if V8_ENABLE_WEBASSEMBLY
  {auto [kind,type]=Stub(StubCallMode::kCallWasmRuntimeStub);require(kind==CallDescriptor::kCallWasmFunction && type.value==22);++checks;}
  const std::array<WasmCallKind,4> kinds{kWasmFunction,kWasmIndirectFunction,kWasmImportWrapper,kWasmCapiFunction};
  const std::array<CallDescriptor::Kind,4> descriptors{CallDescriptor::kCallWasmFunction,CallDescriptor::kCallWasmFunctionIndirect,CallDescriptor::kCallWasmImportWrapper,CallDescriptor::kCallWasmCapiFunction};
  for(unsigned i=0;i<kinds.size();++i) {
   for(uint64_t sig:{uint64_t(0),uint64_t(1),uint64_t(1)<<63,std::numeric_limits<uint64_t>::max()-1}) {
    unsigned before=wasm::SignatureHasher::calls;auto [kind,hash]=Wasm(kinds[i],&sig);
    require(kind==descriptors[i] && hash==(i==1?sig:kInvalidWasmSignatureHash) && wasm::SignatureHasher::calls==before+(i==1));++checks;
   }
  }
#endif
  for(auto mode:{maglev::Call::TargetType::kJSFunction,maglev::Call::TargetType::kAny}) {
   ForwardNode node{mode};require(Forward(&node)==(mode==maglev::Call::TargetType::kJSFunction?Builtin::kCallFunctionForwardVarargs:Builtin::kCallForwardVarargs));++checks;
  }
  for(auto mode:{TypeofMode::kInside,TypeofMode::kNotInside}) {
   GlobalNode node{mode};require(Global(&node)==(mode==TypeofMode::kInside?Builtin::kLoadGlobalICInsideTypeof:Builtin::kLoadGlobalIC));++checks;
  }
  for(unsigned i=0;i<conversions.size();++i) { ConversionNode node{conversions[i]};require(Convert(&node)==primitives[i]);++checks; }
 }
 std::printf("PASS: %u call, comparison and conversion dispatch checks (WASM=%d)\n",checks,V8_ENABLE_WEBASSEMBLY);
}
'''
(out/'control.cc').write_text(header+functions+tests);(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n');shutil.copy2(src/'deps/v8/LICENSE',out/'V8-LICENSE')
runner='''# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
out=Path('/work');results=[]
for wasm in (0,1):
 for mode in ('release','debug'):
  stem=f'{mode}-wasm{wasm}'
  commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra',f'-DV8_ENABLE_WEBASSEMBLY={wasm}']+(['-DDEBUG'] if mode=='debug' else [])+['/work/control.cc','-o','/work/control-'+stem],['/work/control-'+stem],['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/work/'+stem+'-valgrind.log','/work/control-'+stem]]
  for name,command in zip(('compile','normal','memory'),commands):
   with (out/(stem+'-'+name+'.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
   results.append({'name':stem+'-'+name,'command':command,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(results,indent=2)+'\\n');r.check_returncode()
'''
(out/'run.py').write_text(runner)
cmd=['docker','run','--rm','--init','--network','none','--user','1019:100','-v',str(out)+':/work','sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414','python3','-B','-W','error','/work/run.py'];(out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (out/'run.log').open('x') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
