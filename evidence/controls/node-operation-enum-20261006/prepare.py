# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,re,shutil,subprocess
root=Path.cwd();src=root/'work/node-obs-diagnostic-20261006/node-v24.18.1';out=root/'work/node-operation-enum-controls-20261006';out.mkdir();extracts=[]
def take(path,start,end,after=None):
 s=(src/path).read_text();offset=s.index(after) if after else 0;a=s.index(start,offset);b=s.index(end,a);body=s[a:b].rstrip();extracts.append({'file':path,'line':s[:a].count('\n')+1,'body':body,'sha256':hashlib.sha256(body.encode()).hexdigest()});return body
def enum(path,start,after=None):return take(path,start,';',after)+';'
ops='deps/v8/src/compiler/turboshaft/operations.h';mag='deps/v8/src/maglev/maglev-ir.h';turbo='deps/v8/src/compiler/turboshaft/turbolev-graph-builder.cc';x64='deps/v8/src/compiler/backend/x64/instruction-selector-x64.cc'
macro128=take(ops,'#define FOREACH_SIMD_128_LOAD_TRANSFORM_OPCODE','\n\n');macro256=take(ops,'#define FOREACH_SIMD_256_LOAD_TRANSFORM_OPCODE','\n\n')
enum128=enum(ops,'  enum class TransformKind','struct Simd128LoadTransformOp');enum256=enum(ops,'  enum class TransformKind','struct Simd256LoadTransformOp')
body128=take(x64,'  ArchOpcode opcode;','\n  // x64 supports unaligned loads','void InstructionSelectorT::VisitLoadTransform')
body256=take(x64,'  ArchOpcode opcode;','\n  // x64 supports unaligned loads','void InstructionSelectorT::VisitSimd256LoadTransform')
assertmacro=take(mag,'#define ASSERT_CONDITION(V)','\n\n');assertenum=enum(mag,'enum class AssertCondition')
compareenum=enum(ops,'  enum class Kind : uint8_t {','struct ComparisonOp :');comparebody=take(turbo,'    ComparisonOp::Kind kind;','\n    V<Word32> left','  V<Word32> ConvertInt32Compare')
floatmacro=take(mag,'#define IEEE_754_UNARY_LIST(V)','\nclass Float64Ieee754Unary');floatenum=enum(mag,'  enum class Ieee754Function','class Float64Ieee754Unary');floatoutput=enum(ops,'  enum class Kind','struct FloatUnaryOp :');floatbody=take(turbo,'    FloatUnaryOp::Kind kind;','\n    SetMap','Process(maglev::Float64Ieee754Unary*')
shiftenum=enum('deps/v8/src/compiler/machine-operator.h','enum class ShiftKind');shiftoutput=enum(ops,'  enum class Kind','struct ShiftOp :');shiftbody=take('deps/v8/src/compiler/turboshaft/graph-builder.cc','      ShiftOp::Kind kind;','\n      return __ Shift')
arch=sorted(set(re.findall(r'\b(kX64\w+)',body128+body256)))
header='''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Extracted unchanged V8 enum switches with typed output adapters.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <tuple>
#include <utility>
void require(bool value) { if (!value) { std::abort(); } }
'''+macro128+'\n'+macro256+'\n'+assertmacro+'\n'+floatmacro+'\n'
header+='struct Simd128LoadTransformOp {\n'+enum128+'\nTransformKind transform_kind;\n};\nstruct Simd256LoadTransformOp {\n'+enum256+'\nTransformKind transform_kind;\n};\n'
header+='namespace maglev {\n'+assertenum+'\nstruct Float64Ieee754Unary {\n'+floatenum+'\nIeee754Function mode; auto ieee_function() const { return mode; }\n};\n}\n'
header+='struct ComparisonOp {\n'+compareenum+'\n};\nstruct FloatUnaryOp {\n'+floatoutput+'\n};\n'+shiftenum+'\nstruct ShiftOp {\n'+shiftoutput+'\n};\n'
header+='enum ArchOpcode {\n'+',\n'.join(f'{name}={i+1}' for i,name in enumerate(arch))+'\n};\nShiftKind ShiftKindOf(const ShiftKind* op) { return *op; }\n'
functions='__attribute__((noinline)) ArchOpcode Simd128(Simd128LoadTransformOp op) {\n'+body128+'\nreturn opcode;\n}\n'
functions+='__attribute__((noinline)) ArchOpcode Simd256(Simd256LoadTransformOp op) {\n'+body256+'\nreturn opcode;\n}\n'
functions+='__attribute__((noinline)) auto Compare(maglev::AssertCondition condition, bool* negate_result) {\n'+comparebody+'\nreturn std::pair{kind,swap_inputs};\n}\n'
functions+='__attribute__((noinline)) auto Unary(maglev::Float64Ieee754Unary* node) {\n'+floatbody+'\nreturn kind;\n}\n'
functions+='__attribute__((noinline)) auto Shift(const ShiftKind* op) {\n'+shiftbody+'\nreturn kind;\n}\n'
tests=r'''
bool evaluate(ComparisonOp::Kind k, int32_t left, int32_t right) {
 switch(k) {
 case ComparisonOp::Kind::kEqual: return left==right;
 case ComparisonOp::Kind::kSignedLessThan: return left<right;
 case ComparisonOp::Kind::kSignedLessThanOrEqual: return left<=right;
 case ComparisonOp::Kind::kUnsignedLessThan: return uint32_t(left)<uint32_t(right);
 case ComparisonOp::Kind::kUnsignedLessThanOrEqual: return uint32_t(left)<=uint32_t(right);
 }
 std::abort();
}
bool expected(unsigned mode,int32_t a,int32_t b) {
 switch(mode) {
 case 0:return a==b; case 1:return a!=b; case 2:return a<b; case 3:return a<=b;
 case 4:return a>b; case 5:return a>=b; case 6:return uint32_t(a)<uint32_t(b);
 case 7:return uint32_t(a)<=uint32_t(b); case 8:return uint32_t(a)>uint32_t(b);
 case 9:return uint32_t(a)>=uint32_t(b); default:std::abort();
 }
}
int main() {
 using S128=Simd128LoadTransformOp::TransformKind; using S256=Simd256LoadTransformOp::TransformKind;
 const std::array modes128{S128::k8x8S,S128::k8x8U,S128::k16x4S,S128::k16x4U,S128::k32x2S,S128::k32x2U,S128::k8Splat,S128::k16Splat,S128::k32Splat,S128::k64Splat,S128::k32Zero,S128::k64Zero};
 const std::array expected128{kX64S128Load8x8S,kX64S128Load8x8U,kX64S128Load16x4S,kX64S128Load16x4U,kX64S128Load32x2S,kX64S128Load32x2U,kX64S128Load8Splat,kX64S128Load16Splat,kX64S128Load32Splat,kX64S128Load64Splat,kX64Movss,kX64Movsd};
 const std::array modes256{S256::k8x16S,S256::k8x16U,S256::k8x8U,S256::k16x8S,S256::k16x8U,S256::k32x4S,S256::k32x4U,S256::k8Splat,S256::k16Splat,S256::k32Splat,S256::k64Splat};
 const std::array expected256{kX64S256Load8x16S,kX64S256Load8x16U,kX64S256Load8x8U,kX64S256Load16x8S,kX64S256Load16x8U,kX64S256Load32x4S,kX64S256Load32x4U,kX64S256Load8Splat,kX64S256Load16Splat,kX64S256Load32Splat,kX64S256Load64Splat};
 using A=maglev::AssertCondition; const std::array assertions{A::kEqual,A::kNotEqual,A::kLessThan,A::kLessThanEqual,A::kGreaterThan,A::kGreaterThanEqual,A::kUnsignedLessThan,A::kUnsignedLessThanEqual,A::kUnsignedGreaterThan,A::kUnsignedGreaterThanEqual};
 using I=maglev::Float64Ieee754Unary::Ieee754Function; using F=FloatUnaryOp::Kind;
 const std::array unary{
#define ITEM(MathName,ExpName,EnumName) std::pair{I::k##EnumName,F::k##EnumName},
 IEEE_754_UNARY_LIST(ITEM)
#undef ITEM
 };
 const std::array<int32_t,7> boundaries{std::numeric_limits<int32_t>::min(),-65536,-1,0,1,65536,std::numeric_limits<int32_t>::max()};
 unsigned checks=0;
 for(unsigned repeat=0;repeat<1000;++repeat) {
  for(unsigned i=0;i<modes128.size();++i) { require(Simd128({modes128[i]})==expected128[i]);++checks; }
  for(unsigned i=0;i<modes256.size();++i) { require(Simd256({modes256[i]})==expected256[i]);++checks; }
  for(unsigned i=0;i<assertions.size();++i) {
   bool negate=false;auto[kind,swap]=Compare(assertions[i],&negate);
   require(negate==(i==1));require(swap==(i==4||i==5||i==8||i==9));
   for(int32_t left:boundaries) { for(int32_t right:boundaries) {
    int32_t a=left,b=right;if(swap) { std::swap(a,b); }
    require((evaluate(kind,a,b)!=negate)==expected(i,left,right));++checks;
   } }
  }
  for(auto[mode,kind]:unary) { maglev::Float64Ieee754Unary node{mode};require(Unary(&node)==kind);++checks; }
  for(auto mode:{ShiftKind::kNormal,ShiftKind::kShiftOutZeros}) { require(Shift(&mode)==(mode==ShiftKind::kNormal?ShiftOp::Kind::kShiftRightArithmetic:ShiftOp::Kind::kShiftRightArithmeticShiftOutZeros));++checks; }
 }
 std::printf("PASS: %u instruction, comparison, unary and shift dispatch checks\n",checks);
}
'''
(out/'control.cc').write_text(header+functions+tests);(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n');shutil.copy2(src/'deps/v8/LICENSE',out/'V8-LICENSE')
runner='''# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
out=Path('/work');results=[]
for mode in ('release','debug'):
 commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra']+(['-DDEBUG'] if mode=='debug' else [])+['/work/control.cc','-o','/work/control-'+mode],['/work/control-'+mode],['valgrind','--error-exitcode=99','--leak-check=full','--errors-for-leak-kinds=all','--log-file=/work/'+mode+'-valgrind.log','/work/control-'+mode]]
 for name,command in zip(('compile','normal','memory'),commands):
  with (out/(mode+'-'+name+'.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
  results.append({'name':mode+'-'+name,'command':command,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(results,indent=2)+'\\n');r.check_returncode()
'''
(out/'run.py').write_text(runner)
cmd=['docker','run','--rm','--init','--network','none','--user','1019:100','-v',str(out)+':/work','sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414','python3','-B','-W','error','/work/run.py'];(out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (out/'run.log').open('x') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
