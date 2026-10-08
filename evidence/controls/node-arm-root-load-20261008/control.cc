// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
  enum class Kind : uint8_t {
    kWord32,
    kWord64,
    kFloat32,
    kFloat64,
    kSmi,
    kNumber,  // TODO(tebbi): See if we can avoid number constants.
    kTaggedIndex,
    kExternal,
    kHeapObject,
    kCompressedHeapObject,
    kTrustedHeapObject,
    kRelocatableWasmCall,
    kRelocatableWasmStubCall,
    kRelocatableWasmIndirectCallTarget,
    kRelocatableWasmCanonicalSignatureId
  };
 Kind kind=Kind::kWord64;
 struct {uint64_t integral=0;} storage;
 int64_t external=0;
 bool IsIntegral() const {return kind==Kind::kWord32 || kind==Kind::kWord64 || kind==Kind::kRelocatableWasmCanonicalSignatureId;}
 int64_t external_reference() const {return external;}
  int64_t signed_integral() const {
    DCHECK(IsIntegral());
    switch (kind) {
      case Kind::kWord32:
      case Kind::kRelocatableWasmCanonicalSignatureId:
        return static_cast<int32_t>(storage.integral);
      case Kind::kWord64:
        return static_cast<int64_t>(storage.integral);
      default:
        UNREACHABLE();
    }
  }
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
  bool FitsInInt32() const {
    if (type() == kInt32) return true;
    DCHECK(type() == kInt64);
    return value_ >= std::numeric_limits<int32_t>::min() &&
           value_ <= std::numeric_limits<int32_t>::max();
  }
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
  bool MatchSignedIntegralConstant(V<Any> matched, int64_t* constant) const {
    if (const ConstantOp* c = TryCast<ConstantOp>(matched)) {
      if (c->kind == ConstantOp::Kind::kWord32 ||
          c->kind == ConstantOp::Kind::kWord64) {
        *constant = c->signed_integral();
        return true;
      }
    }
    return false;
  }
  bool MatchIntegralZero(V<Any> matched) const {
    int64_t constant;
    return MatchSignedIntegralConstant(matched, &constant) && constant == 0;
  }
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
  InstructionOperand UseImmediate(int immediate) {
    return sequence()->AddImmediate(Constant(immediate));
  }
  InstructionOperand UseImmediate64(int64_t immediate) {
    return sequence()->AddImmediate(Constant(immediate));
  }
 bool CanBeImmediate(int64_t n,ImmediateMode) {return n>=-256 && n<=4095;}
};
static bool TryMatchLoadStoreShift(Arm64OperandGeneratorT*,InstructionSelectorT* selector,MachineRepresentation,OpIndex,OpIndex index,InstructionOperand* reg,InstructionOperand* amount) {
 if(selector->Get(index).tag!=Operation::Tag::Shift) {return false;}
 *reg={InstructionOperand::Register,1};*amount={InstructionOperand::Immediate32,0};return true;
}
void EmitLoad(InstructionSelectorT* selector, OpIndex node,
              InstructionCode opcode, ImmediateMode immediate_mode,
              MachineRepresentation rep, OptionalOpIndex output = {}) {
  Arm64OperandGeneratorT g(selector);
  const LoadOp& load = selector->Get(node).Cast<LoadOp>();

  // The LoadStoreSimplificationReducer transforms all loads into
  // *(base + index).
  OpIndex base = load.base();
  OpIndex index = load.index().value();
  DCHECK_EQ(load.offset, 0);
  DCHECK_EQ(load.element_size_log2, 0);

  InstructionOperand inputs[3];
  size_t input_count = 0;
  InstructionOperand output_op;

  // If output is valid, use that as the output register. This is used when we
  // merge a conversion into the load.
  output_op = g.DefineAsRegister(output.valid() ? output.value() : node);

  const Operation& base_op = selector->Get(base);
  int64_t index_constant;
  const bool is_index_constant =
      selector->MatchSignedIntegralConstant(index, &index_constant);
  if (base_op.Is<Opmask::kExternalConstant>() && is_index_constant) {
    const ConstantOp& constant_base = base_op.Cast<ConstantOp>();
    if (selector->CanAddressRelativeToRootsRegister(
            constant_base.external_reference())) {
      ptrdiff_t const delta =
          index_constant +
          MacroAssemblerBase::RootRegisterOffsetForExternalReference(
              selector->isolate(), constant_base.external_reference());
      input_count = 1;
      // Check that the delta is a 32-bit integer due to the limitations of
      // immediate operands.
      if (is_int32(delta)) {
        inputs[0] = g.UseImmediate(static_cast<int32_t>(delta));
        opcode |= AddressingModeField::encode(kMode_Root);
        selector->Emit(opcode, 1, &output_op, input_count, inputs);
        return;
      }
    }
  }

  if (base_op.Is<LoadRootRegisterOp>()) {
    DCHECK(is_index_constant);
    input_count = 1;
    inputs[0] = g.UseImmediate64(index_constant);
    opcode |= AddressingModeField::encode(kMode_Root);
    selector->Emit(opcode, 1, &output_op, input_count, inputs);
    return;
  }

  inputs[0] = g.UseRegister(base);

  if (is_index_constant) {
    if (g.CanBeImmediate(index_constant, immediate_mode)) {
      input_count = 2;
      inputs[1] = g.UseImmediate64(index_constant);
      opcode |= AddressingModeField::encode(kMode_MRI);
    } else {
      input_count = 2;
      inputs[1] = g.UseRegister(index);
      opcode |= AddressingModeField::encode(kMode_MRR);
    }
  } else {
    if (TryMatchLoadStoreShift(&g, selector, rep, node, index, &inputs[1],
                               &inputs[2])) {
      input_count = 3;
      opcode |= AddressingModeField::encode(kMode_Operand2_R_LSL_I);
    } else {
      input_count = 2;
      inputs[1] = g.UseRegister(index);
      opcode |= AddressingModeField::encode(kMode_MRR);
    }
  }
  selector->Emit(opcode, 1, &output_op, input_count, inputs);
}
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
  bool CanEncodeOffset(int32_t offset, bool tagged_base) const {
    // If the base is tagged we also need to subtract the kHeapObjectTag
    // eventually.
    const int32_t min = kMinOffset + (tagged_base ? kHeapObjectTag : 0);
    if (min <= offset && offset <= kMaxOffset) {
      DCHECK(LoadOp::OffsetIsValid(offset, tagged_base));
      return true;
    }
    return false;
  }
  bool CanEncodeAtomic(OptionalOpIndex index, uint8_t element_size_log2,
                       int32_t offset) const {
    if (element_size_log2 != 0) return false;
    return !(index.has_value() && offset != 0);
  }
  void SimplifyLoadStore(OpIndex& base, OptionalOpIndex& index,
                         LoadOp::Kind& kind, int32_t& offset,
                         uint8_t& element_size_log2) {
    if (element_size_log2 > kMaxElementSizeLog2) {
      DCHECK(index.valid());
      index = __ WordPtrShiftLeft(index.value(), element_size_log2);
      element_size_log2 = 0;
    }

    if (kNeedsUntaggedBase) {
      if (kind.tagged_base) {
        kind.tagged_base = false;
        DCHECK_LE(std::numeric_limits<int32_t>::min() + kHeapObjectTag, offset);
        offset -= kHeapObjectTag;
        base = __ BitcastHeapObjectToWordPtr(base);
      }
    }

    // TODO(nicohartmann@): Remove the case for atomics once crrev.com/c/5237267
    // is ported to x64.
    if (!CanEncodeOffset(offset, kind.tagged_base) ||
        (kind.is_atomic &&
         !CanEncodeAtomic(index, element_size_log2, offset))) {
      // If an index is present, the element_size_log2 is changed to zero.
      // So any load follows the form *(base + offset). To simplify
      // instruction selection, both static and dynamic offsets are stored in
      // the index input.
      // As tagged loads result in modifying the offset by -1, those loads are
      // converted into raw loads (above).
      if (!index.has_value() || matcher_.MatchIntegralZero(index.value())) {
        index = __ IntPtrConstant(offset);
        element_size_log2 = 0;
        offset = 0;
      } else if (element_size_log2 != 0) {
        index = __ WordPtrShiftLeft(index.value(), element_size_log2);
        element_size_log2 = 0;
      }
      if (offset != 0) {
        index = __ WordPtrAdd(index.value(), offset);
        offset = 0;
      }
      DCHECK_EQ(offset, 0);
      DCHECK_EQ(element_size_log2, 0);
    }
  }
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
 std::array<Kind,15> kinds{Kind::kWord32,Kind::kWord64,Kind::kFloat32,Kind::kFloat64,Kind::kSmi,Kind::kNumber,Kind::kTaggedIndex,Kind::kExternal,Kind::kHeapObject,Kind::kCompressedHeapObject,Kind::kTrustedHeapObject,Kind::kRelocatableWasmCall,Kind::kRelocatableWasmStubCall,Kind::kRelocatableWasmIndirectCallTarget,Kind::kRelocatableWasmCanonicalSignatureId};

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
