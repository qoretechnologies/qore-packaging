# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib
import json
import re
import shutil

root = Path('work/node-obs-diagnostic-20261006/node-v24.18.1')
out = Path('work/node-opcode-controls-20261007')
out.mkdir(exist_ok=True)
extracts = []

def take(path, begin, end):
    source = (root / path).read_text()
    start = source.index(begin)
    body = source[start:source.index(end, start)].rstrip()
    extracts.append(dict(file=path, line=source[:start].count('\n') + 1, body=body,
                         sha256=hashlib.sha256(body.encode()).hexdigest()))
    return body

machine = take('deps/v8/src/codegen/machine-type.h', 'enum class MachineRepresentation', '\n\nbool IsSubtype')
load = take('deps/v8/src/compiler/backend/x64/instruction-selector-x64.cc',
            'ArchOpcode GetLoadOpcode(LoadRepresentation', '\nArchOpcode GetStoreOpcode')
kind = take('deps/v8/src/compiler/linkage.h', '  enum Kind {', '\n  };') + '\n  };'
call = take('deps/v8/src/compiler/backend/instruction-selector.cc',
            '  InstructionCode opcode;\n  switch (call_descriptor->kind())', '\n  // Emit the call instruction.')
codes = sorted(set(re.findall(r'\bk(?:X64|Arch)\w+', load + call)))
source = r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
'''+machine+'\nenum ArchOpcode {\n'+',\n'.join(codes)+'\n};\n'+r'''
struct LoadRepresentation {
 MachineRepresentation rep;bool signed_;
 MachineRepresentation representation() const {return rep;}
 bool IsSigned() const {return signed_;}
};
__attribute__((noinline))
'''+load+r'''
using InstructionCode=uint32_t;
struct CallDescriptor {
'''+kind+r'''
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
'''+call+r'''
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
'''
(out / 'control.cc').write_text(source)
(out / 'source-extracts.json').write_text(json.dumps(extracts, indent=2) + '\n')
shutil.copy2(root / 'deps/v8/LICENSE', out / 'V8-LICENSE')
runner = Path('work/node-object-dispatch-controls-20261007/run.py').read_text()
runner = runner.replace("('release','debug')", "('native','compressed')").replace(
    "(['-DDEBUG'] if mode=='debug' else [])", "(['-DV8_COMPRESS_POINTERS'] if mode=='compressed' else [])")
(out / 'run.py').write_text(runner)
