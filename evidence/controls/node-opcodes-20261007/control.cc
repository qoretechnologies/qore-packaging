// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Unchanged V8 opcode dispatch with typed operands and observable encodings.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
void require(bool value) {if(!value) {std::abort();}}
struct Rejected {};
[[noreturn]] void reject() {throw Rejected{};}
#define CHECK(x) do {if(!(x)) {reject();}} while(false)
#define DCHECK(x) require(x)
#define UNREACHABLE() reject()
#define V8_ENABLE_WEBASSEMBLY 1
#define ABI_USES_FUNCTION_DESCRIPTORS 0
#define V8_ENABLE_SANDBOX_BOOL false
enum class MachineRepresentation : uint8_t {
  kNone,
  kBit,
  // Integral representations must be consecutive, in order of increasing order.
  kWord8,
  kWord16,
  kWord32,
  kWord64,
  // (uncompressed) MapWord
  // kMapWord is the representation of a map word, i.e. a map in the header
  // of a HeapObject.
  // If V8_MAP_PACKING is disabled, a map word is just the map itself. Hence
  //     kMapWord is equivalent to kTaggedPointer -- in fact it will be
  //     translated to kTaggedPointer during memory lowering.
  // If V8_MAP_PACKING is enabled, a map word is a Smi-like encoding of a map
  //     and some meta data. Memory lowering of kMapWord loads/stores
  //     produces low-level kTagged loads/stores plus the necessary
  //     decode/encode operations.
  // In either case, the kMapWord representation is not used after memory
  // lowering.
  kMapWord,
  kTaggedSigned,       // (uncompressed) Smi
  kTaggedPointer,      // (uncompressed) HeapObject
  kTagged,             // (uncompressed) Object (Smi or HeapObject)
  kCompressedPointer,  // (compressed) HeapObject
  kCompressed,         // (compressed) Object (Smi or HeapObject)
  kProtectedPointer,   // (uncompressed) TrustedObject
  kIndirectPointer,    // (indirect) HeapObject
  // A 64-bit pointer encoded in a way (e.g. as offset) that guarantees it will
  // point into the sandbox.
  kSandboxedPointer,
  // kFloat16RawBits is not a real FP representation! It's representation of a
  // float16 bitcast to a word16, and is used for conversions to and from
  // Float16Array elements. It is not used after machine lowering.
  kFloat16RawBits,
  // FP and SIMD representations must be last, and in order of increasing size.
  kFloat16,
  kFloat32,
  kFloat64,
  kSimd128,
  kSimd256,
  kFirstFPRepresentation = kFloat16,
  kLastRepresentation = kSimd256
};
enum ArchOpcode {
kArchCallBuiltinPointer,
kArchCallCFunction,
kArchCallCFunctionWithFrameState,
kArchCallCodeObject,
kArchCallJSFunction,
kArchCallWasmFunction,
kArchCallWasmFunctionIndirect,
kX64Movdqu,
kX64Movdqu256,
kX64Movl,
kX64Movq,
kX64MovqDecodeSandboxedPointer,
kX64MovqDecompressProtected,
kX64MovqDecompressTagged,
kX64MovqDecompressTaggedSigned,
kX64Movsd,
kX64Movsh,
kX64Movss,
kX64Movsxbl,
kX64Movsxwl,
kX64Movzxbl,
kX64Movzxwl
};

struct LoadRepresentation {
 MachineRepresentation rep;bool signed_;
 MachineRepresentation representation() const {return rep;}
 bool IsSigned() const {return signed_;}
};
__attribute__((noinline))
ArchOpcode GetLoadOpcode(LoadRepresentation load_rep) {
  ArchOpcode opcode;
  switch (load_rep.representation()) {
    case MachineRepresentation::kFloat16:
      opcode = kX64Movsh;
      break;
    case MachineRepresentation::kFloat32:
      opcode = kX64Movss;
      break;
    case MachineRepresentation::kFloat64:
      opcode = kX64Movsd;
      break;
    case MachineRepresentation::kBit:  // Fall through.
    case MachineRepresentation::kWord8:
      opcode = load_rep.IsSigned() ? kX64Movsxbl : kX64Movzxbl;
      break;
    case MachineRepresentation::kWord16:
      opcode = load_rep.IsSigned() ? kX64Movsxwl : kX64Movzxwl;
      break;
    case MachineRepresentation::kWord32:
      opcode = kX64Movl;
      break;
    case MachineRepresentation::kCompressedPointer:  // Fall through.
    case MachineRepresentation::kCompressed:
#ifdef V8_COMPRESS_POINTERS
      opcode = kX64Movl;
      break;
#else
      UNREACHABLE();
#endif
#ifdef V8_COMPRESS_POINTERS
    case MachineRepresentation::kTaggedSigned:
      opcode = kX64MovqDecompressTaggedSigned;
      break;
    case MachineRepresentation::kTaggedPointer:
    case MachineRepresentation::kTagged:
      opcode = kX64MovqDecompressTagged;
      break;
#else
    case MachineRepresentation::kTaggedSigned:   // Fall through.
    case MachineRepresentation::kTaggedPointer:  // Fall through.
    case MachineRepresentation::kTagged:         // Fall through.
#endif
    case MachineRepresentation::kWord64:
      opcode = kX64Movq;
      break;
    case MachineRepresentation::kProtectedPointer:
      CHECK(V8_ENABLE_SANDBOX_BOOL);
      opcode = kX64MovqDecompressProtected;
      break;
    case MachineRepresentation::kSandboxedPointer:
      opcode = kX64MovqDecodeSandboxedPointer;
      break;
    case MachineRepresentation::kSimd128:
      opcode = kX64Movdqu;
      break;
    case MachineRepresentation::kSimd256:  // Fall through.
      opcode = kX64Movdqu256;
      break;
    case MachineRepresentation::kNone:     // Fall through.
    case MachineRepresentation::kMapWord:  // Fall through.
    case MachineRepresentation::kIndirectPointer:  // Fall through.
    case MachineRepresentation::kFloat16RawBits:
      UNREACHABLE();
  }
  return opcode;
}
using InstructionCode=uint32_t;
struct CallDescriptor {
  enum Kind {
    kCallCodeObject,         // target is a Code object
    kCallJSFunction,         // target is a JSFunction object
    kCallAddress,            // target is a machine pointer
#if V8_ENABLE_WEBASSEMBLY    // ↓ WebAssembly only
    kCallWasmCapiFunction,   // target is a Wasm C API function
    kCallWasmFunction,       // target is a wasm function
    kCallWasmFunctionIndirect,  // target is a wasm function that will be called
                                // indirectly
    kCallWasmImportWrapper,     // target is a wasm import wrapper
#endif                       // ↑ WebAssembly only
    kCallBuiltinPointer,     // target is a builtin pointer
  };
 Kind value;unsigned gp,fp;
 Kind kind() const {return value;}
 unsigned GPParameterCount() const {return gp;}
 unsigned FPParameterCount() const {return fp;}
};
struct ParamField {static unsigned encode(int value) {require(value>=0&&value<256);return static_cast<unsigned>(value)<<8;}};
struct FPParamField {static unsigned encode(int value) {require(value>=0&&value<256);return static_cast<unsigned>(value)<<16;}};
unsigned EncodeCallDescriptorFlags(ArchOpcode opcode, unsigned flags) {return static_cast<unsigned>(opcode)|(flags<<24);}
struct CallOp {bool relocatable;bool callee() const {return relocatable;}};
struct Selector {
 bool IsRelocatableWasmConstant(bool value) const {return value;}
 __attribute__((noinline)) InstructionCode choose(const CallDescriptor* call_descriptor, bool needs_frame_state,
                                                  unsigned flags, const CallOp& call_op) const {
  InstructionCode opcode;
  switch (call_descriptor->kind()) {
    case CallDescriptor::kCallAddress: {
      int gp_param_count =
          static_cast<int>(call_descriptor->GPParameterCount());
      int fp_param_count =
          static_cast<int>(call_descriptor->FPParameterCount());
#if ABI_USES_FUNCTION_DESCRIPTORS
      // Highest fp_param_count bit is used on AIX to indicate if a CFunction
      // call has function descriptor or not.
      static_assert(FPParamField::kSize == kHasFunctionDescriptorBitShift + 1);
      if (!call_descriptor->NoFunctionDescriptor()) {
        fp_param_count |= 1 << kHasFunctionDescriptorBitShift;
      }
#endif
      opcode = needs_frame_state ? kArchCallCFunctionWithFrameState
                                 : kArchCallCFunction;
      opcode |= ParamField::encode(gp_param_count) |
                FPParamField::encode(fp_param_count);
      break;
    }
    case CallDescriptor::kCallCodeObject:
      opcode = EncodeCallDescriptorFlags(kArchCallCodeObject, flags);
      break;
    case CallDescriptor::kCallJSFunction:
      opcode = EncodeCallDescriptorFlags(kArchCallJSFunction, flags);
      break;
#if V8_ENABLE_WEBASSEMBLY
    case CallDescriptor::kCallWasmCapiFunction:
    case CallDescriptor::kCallWasmFunction:
    case CallDescriptor::kCallWasmImportWrapper:
      DCHECK(this->IsRelocatableWasmConstant(call_op.callee()));
      opcode = EncodeCallDescriptorFlags(kArchCallWasmFunction, flags);
      break;
    case CallDescriptor::kCallWasmFunctionIndirect:
      DCHECK(!this->IsRelocatableWasmConstant(call_op.callee()));
      opcode = EncodeCallDescriptorFlags(kArchCallWasmFunctionIndirect, flags);
      break;
#endif  // V8_ENABLE_WEBASSEMBLY
    case CallDescriptor::kCallBuiltinPointer:
      opcode = EncodeCallDescriptorFlags(kArchCallBuiltinPointer, flags);
      break;
  }
 return opcode;
 }
};
int main() {
 unsigned checks=0;
 using M=MachineRepresentation;
 struct LoadCase {M rep;ArchOpcode unsigned_code,signed_code;bool rejected;};
#ifdef V8_COMPRESS_POINTERS
 constexpr ArchOpcode tagged_signed=kX64MovqDecompressTaggedSigned,tagged=kX64MovqDecompressTagged;
 constexpr bool compressed_rejected=false;
#else
 constexpr ArchOpcode tagged_signed=kX64Movq,tagged=kX64Movq;
 constexpr bool compressed_rejected=true;
#endif
 const std::array cases{
  LoadCase{M::kNone,kX64Movq,kX64Movq,true},LoadCase{M::kBit,kX64Movzxbl,kX64Movsxbl,false},
  LoadCase{M::kWord8,kX64Movzxbl,kX64Movsxbl,false},LoadCase{M::kWord16,kX64Movzxwl,kX64Movsxwl,false},
  LoadCase{M::kWord32,kX64Movl,kX64Movl,false},LoadCase{M::kWord64,kX64Movq,kX64Movq,false},
  LoadCase{M::kMapWord,kX64Movq,kX64Movq,true},LoadCase{M::kTaggedSigned,tagged_signed,tagged_signed,false},
  LoadCase{M::kTaggedPointer,tagged,tagged,false},LoadCase{M::kTagged,tagged,tagged,false},
  LoadCase{M::kCompressedPointer,kX64Movl,kX64Movl,compressed_rejected},
  LoadCase{M::kCompressed,kX64Movl,kX64Movl,compressed_rejected},
  LoadCase{M::kProtectedPointer,kX64Movq,kX64Movq,true},LoadCase{M::kIndirectPointer,kX64Movq,kX64Movq,true},
  LoadCase{M::kSandboxedPointer,kX64MovqDecodeSandboxedPointer,kX64MovqDecodeSandboxedPointer,false},
  LoadCase{M::kFloat16RawBits,kX64Movq,kX64Movq,true},LoadCase{M::kFloat16,kX64Movsh,kX64Movsh,false},
  LoadCase{M::kFloat32,kX64Movss,kX64Movss,false},LoadCase{M::kFloat64,kX64Movsd,kX64Movsd,false},
  LoadCase{M::kSimd128,kX64Movdqu,kX64Movdqu,false},LoadCase{M::kSimd256,kX64Movdqu256,kX64Movdqu256,false}
 };
 require(cases.size()==static_cast<unsigned>(M::kLastRepresentation)+1);
 using C=CallDescriptor;
 const std::array kinds{C::kCallCodeObject,C::kCallJSFunction,C::kCallAddress,C::kCallWasmCapiFunction,
     C::kCallWasmFunction,C::kCallWasmFunctionIndirect,C::kCallWasmImportWrapper,C::kCallBuiltinPointer};
 const std::array opcodes{kArchCallCodeObject,kArchCallJSFunction,kArchCallCFunction,kArchCallWasmFunction,
     kArchCallWasmFunction,kArchCallWasmFunctionIndirect,kArchCallWasmFunction,kArchCallBuiltinPointer};
 Selector selector;
 for(unsigned repeat=0;repeat<1000;++repeat) {
  for(auto test:cases) {for(bool signed_:{false,true}) {
   bool rejected=false;
   try {auto actual=GetLoadOpcode({test.rep,signed_});require(!test.rejected);require(actual==(signed_?test.signed_code:test.unsigned_code));}
   catch(const Rejected&) {rejected=true;}
   require(rejected==test.rejected);++checks;
  }}
  for(unsigned i=0;i<kinds.size();++i) {for(bool frame:{false,true}) {
   for(unsigned gp:{0u,1u,8u,255u}) {for(unsigned fp:{0u,1u,8u,255u}) {for(unsigned flags:{0u,1u,127u}) {
    C descriptor{kinds[i],gp,fp};CallOp op{i==3||i==4||i==6};
    unsigned result=selector.choose(&descriptor,frame,flags,op);
    unsigned expected=i==2?(static_cast<unsigned>(frame?kArchCallCFunctionWithFrameState:kArchCallCFunction)|(gp<<8)|(fp<<16))
                          :(static_cast<unsigned>(opcodes[i])|(flags<<24));
    require(result==expected);++checks;
   }}}
  }}
 }
 std::printf("PASS: %u call and load opcode checks\n",checks);
}
