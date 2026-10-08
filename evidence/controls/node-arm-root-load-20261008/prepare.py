# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,re,shutil,subprocess
root=Path.cwd();source=root/'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1';out=root/'work/node-arm-root-load-20261008';out.mkdir();extracts=[]
def take(file,start,end,after=''):
 s=(source/file).read_text();a=s.index(start,s.index(after) if after else 0);b=s.index(end,a)+len(end);v=s[a:b]
 extracts.append({'file':file,'line':s[:a].count('\n')+1,'text':v,'sha256':hashlib.sha256(v.encode()).hexdigest()});return v
ops='deps/v8/src/compiler/turboshaft/operations.h';matcher='deps/v8/src/compiler/turboshaft/operation-matcher.h';selector='deps/v8/src/compiler/backend/arm64/instruction-selector-arm64.cc';impl='deps/v8/src/compiler/backend/instruction-selector-impl.h';instruction='deps/v8/src/compiler/backend/instruction.h';simplification='deps/v8/src/compiler/turboshaft/load-store-simplification-reducer.h'
kind=take(ops,'  enum class Kind : uint8_t {','\n  };','struct ConstantOp :')
signed=take(ops,'  int64_t signed_integral() const {','\n  }','struct ConstantOp :')
match=take(matcher,'  bool MatchSignedIntegralConstant(','\n  }');zero=take(matcher,'  bool MatchIntegralZero(','\n  }')
fits=take(instruction,'  bool FitsInInt32() const {','\n  }')
use32=take(impl,'  InstructionOperand UseImmediate(int immediate) {','\n  }');use64=take(impl,'  InstructionOperand UseImmediate64(int64_t immediate) {','\n  }')
emit=take(selector,'void EmitLoad(InstructionSelectorT* selector, OpIndex node,','\n}')
simple=take(simplification,'  void SimplifyLoadStore(OpIndex& base,','\n  }')
canoffset=take(simplification,'  bool CanEncodeOffset(int32_t offset,','\n  }');canatomic=take(simplification,'  bool CanEncodeAtomic(OptionalOpIndex index,','\n  }')
cpp=r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Unchanged V8 matcher, simplifier, load selector, immediate wrappers and range predicate.
// Graph and emitter adapters preserve branch inputs; no ARM instructions are executed.
#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <optional>
#include <type_traits>
struct Rejected {};
#define CHECK(x) do { if (!(x)) { throw Rejected{}; } } while(false)
#define UNREACHABLE() do { throw Rejected{}; } while(false)
#ifdef DEBUG
#define DCHECK(x) CHECK(x)
#else
#define DCHECK(x) ((void)sizeof(x))
#endif
#define DCHECK_EQ(a,b) DCHECK((a)==(b))
#define DCHECK_LE(a,b) DCHECK((a)<=(b))
struct OpIndex {int id=-1; bool valid() const {return id>=0;} bool operator==(const OpIndex&) const = default;};
struct OptionalOpIndex {
 std::optional<OpIndex> index;
 OptionalOpIndex()=default;OptionalOpIndex(OpIndex value):index(value) {}
 bool valid() const {return index.has_value();}bool has_value() const {return valid();}
 OpIndex value() const {CHECK(valid());return *index;}
};
struct Any {};template<class>using V=OpIndex;
struct LoadRootRegisterOp {};namespace Opmask {struct kExternalConstant {};}
struct ConstantOp {
'''+kind+r'''
 Kind kind=Kind::kWord64;
 struct {uint64_t integral=0;} storage;
 int64_t external=0;
 bool IsIntegral() const {return kind==Kind::kWord32 || kind==Kind::kWord64 || kind==Kind::kRelocatableWasmCanonicalSignatureId;}
 int64_t external_reference() const {return external;}
'''+signed+r'''
};
struct LoadOp {
 struct Kind {bool tagged_base=false;bool is_atomic=false;};
 OpIndex base_index{0};OptionalOpIndex index_value{OpIndex{1}};
 int32_t offset=0;uint8_t element_size_log2=0;
 OpIndex base() const {return base_index;}OptionalOpIndex index() const {return index_value;}
 static bool OffsetIsValid(int32_t offset,bool tagged) {return !tagged || offset>std::numeric_limits<int32_t>::min();}
};
struct Operation {
 enum class Tag {Root,Constant,Load,Dynamic,Shift};Tag tag=Tag::Dynamic;
 ConstantOp constant;LoadOp load;
 template<class T>bool Is() const {
  if constexpr(std::is_same_v<T,LoadRootRegisterOp>) {return tag==Tag::Root;}
  else if constexpr(std::is_same_v<T,Opmask::kExternalConstant>) {return tag==Tag::Constant && constant.kind==ConstantOp::Kind::kExternal;}
  else {return false;}
 }
 template<class T>const T& Cast() const {
  if constexpr(std::is_same_v<T,LoadOp>) {CHECK(tag==Tag::Load);return load;}
  else {CHECK(tag==Tag::Constant);return constant;}
 }
};
class Constant {
 public:
 enum Type {kInt32,kInt64};
 explicit Constant(int32_t value):type_(kInt32),value_(value) {}
 explicit Constant(int64_t value):type_(kInt64),value_(value) {}
 Type type() const {return type_;}int64_t value() const {return value_;}
'''+fits+r'''
 private:Type type_;int64_t value_;
};
struct InstructionOperand {enum Kind {Register,Immediate32,Immediate64};Kind kind=Register;int64_t value=0;bool operator==(const InstructionOperand&)const=default;};
using InstructionCode=unsigned;
enum ImmediateMode {kLoadStoreImm8};enum MachineRepresentation {kWord8};
enum AddressingMode {kMode_Root=1,kMode_MRI=2,kMode_MRR=3,kMode_Operand2_R_LSL_I=4};
struct AddressingModeField {static unsigned encode(AddressingMode mode) {return static_cast<unsigned>(mode)<<8;}};
static bool is_int32(int64_t n) {return n>=INT32_MIN && n<=INT32_MAX;}
struct InstructionSelectorT {
 std::array<Operation,4> graph;bool allow_relative=true;unsigned emitted=0;unsigned opcode=0;
 InstructionOperand output;std::array<InstructionOperand,3> inputs{};size_t count=0;
 const Operation& Get(OpIndex idx) const {CHECK(idx.id>=0 && idx.id<4);return graph[idx.id];}
 template<class T>const T* TryCast(OpIndex idx) const {
  static_assert(std::is_same_v<T,ConstantOp>);const auto& op=Get(idx);return op.tag==Operation::Tag::Constant?&op.constant:nullptr;
 }
'''+match+'\n'+zero+r'''
 bool CanAddressRelativeToRootsRegister(int64_t) const {return allow_relative;}
 void* isolate() const {return nullptr;}
 InstructionOperand AddImmediate(const Constant& c) {return {c.FitsInInt32()?InstructionOperand::Immediate32:InstructionOperand::Immediate64,c.value()};}
 void Emit(unsigned code,size_t outputs,const InstructionOperand* result,size_t size,const InstructionOperand* values) {
  CHECK(outputs==1 && size>=1 && size<=3);++emitted;opcode=code;output=*result;count=size;
  for(size_t i=0;i<size;++i) {inputs[i]=values[i];}
 }
};
struct MacroAssemblerBase {static int64_t RootRegisterOffsetForExternalReference(void*,int64_t external) {return external;}};
struct Arm64OperandGeneratorT {
 InstructionSelectorT* selector;explicit Arm64OperandGeneratorT(InstructionSelectorT* s):selector(s){}
 InstructionSelectorT* sequence() {return selector;}
 InstructionOperand DefineAsRegister(OpIndex n) {return {InstructionOperand::Register,n.id};}
 InstructionOperand UseRegister(OpIndex n) {return {InstructionOperand::Register,n.id};}
'''+use32+'\n'+use64+r'''
 bool CanBeImmediate(int64_t n,ImmediateMode) {return n>=-256 && n<=4095;}
};
static bool TryMatchLoadStoreShift(Arm64OperandGeneratorT*,InstructionSelectorT* selector,MachineRepresentation,OpIndex,OpIndex index,InstructionOperand* reg,InstructionOperand* amount) {
 if(selector->Get(index).tag!=Operation::Tag::Shift) {return false;}
 *reg={InstructionOperand::Register,1};*amount={InstructionOperand::Immediate32,0};return true;
}
'''+emit+r'''
struct Simplifier {
 InstructionSelectorT& matcher_;explicit Simplifier(InstructionSelectorT& selector):matcher_(selector) {}
 static constexpr bool kNeedsUntaggedBase=true;static constexpr int kMinOffset=1,kMaxOffset=0,kMaxElementSizeLog2=0,kHeapObjectTag=1;
 OpIndex IntPtrConstant(int64_t value) {
  auto& op=matcher_.graph[1];op.tag=Operation::Tag::Constant;op.constant.kind=ConstantOp::Kind::kWord64;op.constant.storage.integral=static_cast<uint64_t>(value);return OpIndex{1};
 }
 OpIndex WordPtrShiftLeft(OpIndex index,uint8_t shift) {
  int64_t value;if(matcher_.MatchSignedIntegralConstant(index,&value)) {return IntPtrConstant(std::bit_cast<int64_t>(static_cast<uint64_t>(value)<<shift));}
  matcher_.graph[1].tag=Operation::Tag::Dynamic;return OpIndex{1};
 }
 OpIndex WordPtrAdd(OpIndex index,int32_t offset) {
  int64_t value;if(matcher_.MatchSignedIntegralConstant(index,&value)) {return IntPtrConstant(std::bit_cast<int64_t>(static_cast<uint64_t>(value)+static_cast<uint64_t>(offset)));}
  matcher_.graph[1].tag=Operation::Tag::Dynamic;return OpIndex{1};
 }
 OpIndex BitcastHeapObjectToWordPtr(OpIndex base) {return base;}
#define __ this->
'''+canoffset+'\n'+canatomic+'\n'+simple+r'''
#undef __
};
static unsigned checks=0,rejected=0;
static void require(bool ok) {++checks;if(!ok) {std::fprintf(stderr,"FAIL check %u\n",checks);std::abort();}}
static InstructionSelectorT setup(Operation::Tag base,ConstantOp::Kind kind,int64_t value) {
 InstructionSelectorT s;s.graph[0].tag=base;s.graph[0].constant.kind=ConstantOp::Kind::kExternal;
 s.graph[1].tag=Operation::Tag::Constant;s.graph[1].constant.kind=kind;s.graph[1].constant.storage.integral=static_cast<uint64_t>(value);
 s.graph[2].tag=Operation::Tag::Load;return s;
}
static void check_result(const InstructionSelectorT& s,AddressingMode mode,size_t count,OpIndex output) {
 require(s.emitted==1 && s.opcode==(17U|AddressingModeField::encode(mode)) && s.count==count);
 require(s.output==InstructionOperand{InstructionOperand::Register,output.id});
}
static void run(InstructionSelectorT& s,OptionalOpIndex output={}) {EmitLoad(&s,OpIndex{2},17,kLoadStoreImm8,kWord8,output);}
int main() {
 using Tag=Operation::Tag;using Kind=ConstantOp::Kind;
 std::array<int64_t,17> values{INT64_MIN,-4294967296LL,-2147483649LL,INT32_MIN,-4096,-257,-256,-1,0,1,255,4095,4096,INT32_MAX,2147483648LL,4294967295LL,INT64_MAX};
 for(auto kind:{Kind::kWord32,Kind::kWord64}) {
  for(int64_t raw:values) {
   int64_t expected=kind==Kind::kWord32?static_cast<int32_t>(raw):raw;
   if(kind==Kind::kWord32 && (raw<INT32_MIN || raw>4294967295LL)) {continue;}
   for(bool output_override:{false,true}) {
    OptionalOpIndex output=output_override?OptionalOpIndex{OpIndex{3}}:OptionalOpIndex{};
    auto root=setup(Tag::Root,kind,raw);run(root,output);check_result(root,kMode_Root,1,OpIndex{output_override?3:2});
    require(root.inputs[0].value==expected && root.inputs[0].kind==(is_int32(expected)?InstructionOperand::Immediate32:InstructionOperand::Immediate64));
    auto general=setup(Tag::Dynamic,kind,raw);run(general,output);
    bool immediate=expected>=-256 && expected<=4095;check_result(general,immediate?kMode_MRI:kMode_MRR,2,OpIndex{output_override?3:2});
    require(general.inputs[0]==InstructionOperand{InstructionOperand::Register,0});
    require(general.inputs[1]==(immediate?InstructionOperand{InstructionOperand::Immediate32,expected}:InstructionOperand{InstructionOperand::Register,1}));
   }
  }
 }
 // Root producers provide raw integer offsets; ARM simplification moves them into a WordPtr constant index.
 for(int32_t offset:{INT32_MIN,-4096,-1,0,1,4096,INT32_MAX}) {
  for(bool atomic:{false,true}) {
   auto s=setup(Tag::Root,Kind::kWord64,0);OpIndex base{0};OptionalOpIndex index;LoadOp::Kind kind{false,atomic};int32_t remaining=offset;uint8_t scale=0;
   Simplifier(s).SimplifyLoadStore(base,index,kind,remaining,scale);
   require(remaining==0 && scale==0 && base.id==0 && index.has_value());s.graph[2].load.index_value=index;
   run(s);check_result(s,kMode_Root,1,OpIndex{2});require(s.inputs[0]==InstructionOperand{InstructionOperand::Immediate32,offset});
  }
 }
 // External root-relative addressing: exact 32-bit boundary and fallback, without signed addition overflow.
 for(int64_t value:{-2147483649LL,-2147483648LL,-1LL,0LL,1LL,2147483647LL,2147483648LL}) {
  for(int64_t delta:{-16LL,0LL,16LL}) {
   for(bool allowed:{false,true}) {
    auto s=setup(Tag::Constant,Kind::kWord64,value);s.graph[0].constant.external=delta;s.allow_relative=allowed;run(s);
    if(allowed && is_int32(value+delta)) {check_result(s,kMode_Root,1,OpIndex{2});require(s.inputs[0]==InstructionOperand{InstructionOperand::Immediate32,value+delta});}
    else {bool immediate=value>=-256 && value<=4095;check_result(s,immediate?kMode_MRI:kMode_MRR,2,OpIndex{2});require(s.inputs[1]==(immediate?InstructionOperand{InstructionOperand::Immediate32,value}:InstructionOperand{InstructionOperand::Register,1}));}
   }
  }
 }
 for(Tag base:{Tag::Dynamic,Tag::Constant}) {
  for(Tag index:{Tag::Dynamic,Tag::Shift}) {
   auto s=setup(base,Kind::kWord64,0);s.graph[1].tag=index;run(s);
   check_result(s,index==Tag::Shift?kMode_Operand2_R_LSL_I:kMode_MRR,index==Tag::Shift?3:2,OpIndex{2});
   require(s.inputs[0]==InstructionOperand{InstructionOperand::Register,0});
  }
 }
'''
names=re.findall(r'^    (k\w+)[,\n]',kind,re.M);assert len(names)==15,names
cpp+=' std::array<Kind,15> kinds{'+','.join('Kind::'+name for name in names)+'};\n'
cpp+=r'''
 for(Kind kind:kinds) {
  if(kind==Kind::kWord32 || kind==Kind::kWord64) {continue;}
  auto s=setup(Tag::Root,kind,7);int64_t sentinel=987654321;require(!s.MatchSignedIntegralConstant(OpIndex{1},&sentinel) && sentinel==987654321);
#ifdef DEBUG
  bool caught=false;try {run(s);} catch(const Rejected&) {caught=true;++rejected;}
  require(caught && s.emitted==0);
#endif
 }
#ifdef DEBUG
 auto dynamic=setup(Tag::Root,Kind::kWord64,0);dynamic.graph[1].tag=Tag::Dynamic;
 bool caught=false;try {run(dynamic);} catch(const Rejected&) {caught=true;++rejected;}
 require(caught && dynamic.emitted==0);
#endif
 std::printf("PASS: %u root-load checks; %u invalid root-index cases rejected\n",checks,rejected);
}
'''
(out/'control.cc').write_text(cpp);(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n');shutil.copy2(source/'deps/v8/LICENSE',out/'V8-LICENSE')
runner='''# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
out=Path('/control');records=[]
for mode in ['release','debug']:
 flags=['-DNDEBUG'] if mode=='release' else ['-DDEBUG']
 commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra',*flags,'/control/control.cc','-o','/control/'+mode],['/control/'+mode],['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','/control/'+mode]]
 for name,command in zip(['compile','normal','valgrind'],commands):
  with (out/(mode+'-'+name+'.log')).open('x') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
  records.append({'name':mode+'-'+name,'command':command,'exit_code':r.returncode});(out/'status.json').write_text(json.dumps(records,indent=2)+'\\n');r.check_returncode()
'''
(out/'run.py').write_text(runner)
subprocess.run(['docker','run','--rm','--network','none','--user','1019:100','-v',str(out)+':/control','sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414','python3','-B','-W','error','/control/run.py'],check=True)
