# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess

root=Path.cwd()
source=root/'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
out=root/'work/node-arm-memory-control-20261008'
out.mkdir()
extracts=[]
def take(file, begin, end, after=''):
    s=(source/file).read_text()
    a=s.index(begin,s.index(after) if after else 0)
    b=s.index(end,a)+len(end)
    value=s[a:b]
    extracts.append({'file':file,'line':s[:a].count('\n')+1,'text':value,'sha256':hashlib.sha256(value.encode()).hexdigest()})
    return value
machine_file='deps/v8/src/codegen/machine-type.h'
rep_file='deps/v8/src/compiler/turboshaft/representations.h'
selector='deps/v8/src/compiler/backend/arm64/instruction-selector-arm64.cc'
machine=take(machine_file,'enum class MachineRepresentation','\n};')
semantic=take(machine_file,'enum class MachineSemantic','\n};')
unsigned=take(machine_file,'  constexpr bool IsUnsigned() const','\n  }')
memory=take(rep_file,'  enum class Enum : uint8_t','\n  };','class MemoryRepresentation {')
maybe=take(rep_file,'  enum class Enum : uint8_t','\n  };','class MaybeRegisterRepresentation {')
register=take(rep_file,'  enum class Enum : uint8_t','\n  };','class RegisterRepresentation :')
immediate=take(selector,'enum ImmediateMode','\n};')
store=take(selector,'std::tuple<InstructionCode, ImmediateMode> GetStoreOpcodeAndImmediate(','\n}')
load=take(selector,'std::tuple<InstructionCode, ImmediateMode> GetLoadOpcodeAndImmediate(','\n}')
legacy=take(selector,'std::tuple<InstructionCode, ImmediateMode> GetLoadOpcodeAndImmediate(\n    LoadRepresentation','\n}')
mem_names=re.findall(r'^    k(\w+)[,\n]',memory,re.M)
reg_names=re.findall(r'^    k(\w+)\s*=',register,re.M)
machine_names=re.findall(r'^  k(\w+)\s*[,/]',machine,re.M)
semantic_names=re.findall(r'^  k(\w+)[,\n]',semantic,re.M)
assert len(mem_names)==22 and len(reg_names)==8 and len(semantic_names)==11
opcodes=sorted(set(re.findall(r'\bkArm64\w+',store+load+legacy)))
text='''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// V8 enum declarations and selector bodies are unchanged BSD-licensed extracts.
// Adapters preserve typed representation values and opcode identities. Fatal
// checks throw only in this standalone control so rejection paths can be counted.
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <optional>
#include <tuple>
struct Rejected {};
#define CHECK(x) do { if (!(x)) { throw Rejected{}; } } while (false)
#define UNREACHABLE() do { throw Rejected{}; } while (false)
#ifdef DEBUG
#define DCHECK_EQ(a,b) CHECK((a)==(b))
#else
// Keep adapter types checked without evaluating a release-mode assertion.
#define DCHECK_EQ(a,b) ((void)sizeof((a)==(b)))
#endif
#ifdef V8_COMPRESS_POINTERS
constexpr bool COMPRESS_POINTERS_BOOL=true;
#else
constexpr bool COMPRESS_POINTERS_BOOL=false;
#endif
constexpr bool V8_ENABLE_SANDBOX_BOOL=SANDBOX;
'''+machine+'\n'+semantic+'\n'+immediate+'\n'
text+='enum InstructionCode { '+', '.join(opcodes)+' };\n'
text+='struct MaybeRegisterRepresentation {\n'+maybe+'\n};\n'
for cls,enum,names in [('MemoryRepresentation',memory,mem_names),('RegisterRepresentation',register,reg_names)]:
    text+='class '+cls+' {\npublic:\n'+enum+'\n'
    text+=f'explicit constexpr {cls}(Enum value):value_(value) {{}}\nconstexpr operator Enum() const {{ return value_; }}\n'
    for name in names:
        text+=f'static constexpr {cls} {name}() {{ return {cls}(Enum::k{name}); }}\n'
    text+='private:\nEnum value_;\n};\n'
text+='''constexpr int ElementSizeLog2Of(MachineRepresentation) { return COMPRESS_POINTERS_BOOL ? 2 : 3; }
struct LoadRepresentation {
    MachineRepresentation rep;
    MachineSemantic sem;
    MachineRepresentation representation() const { return rep; }
    constexpr MachineSemantic semantic() const { return sem; }
'''+unsigned+'\n};\n'+store+'\n'+load+'\n'+legacy+'\n'
text+='''using Result=std::tuple<InstructionCode,ImmediateMode>;
static unsigned checks=0, rejected=0;
template<class F> void check(const char* label, std::optional<Result> expected, F invoke) {
    try {
        auto actual=invoke();
        if (!expected || actual!=*expected) { std::fprintf(stderr,"FAIL result: %s\\n",label); std::abort(); }
    } catch (const Rejected&) {
        if (expected) { std::fprintf(stderr,"FAIL rejection: %s\\n",label); std::abort(); }
        ++rejected;
    }
    ++checks;
}
int main() {
'''
def pair(op,imm): return 'Result{kArm64'+op+', k'+imm+'}'
store_table={
    'Int8':('Strb','LoadStoreImm8',False),'Uint8':('Strb','LoadStoreImm8',False),
    'Int16':('Strh','LoadStoreImm16',False),'Uint16':('Strh','LoadStoreImm16',False),
    'Int32':('StrW','LoadStoreImm32','StrWPair'),'Uint32':('StrW','LoadStoreImm32','StrWPair'),
    'Int64':('Str','LoadStoreImm64','StrPair'),'Uint64':('Str','LoadStoreImm64','StrPair'),
    'Float16':('StrH','LoadStoreImm16',False),'Float32':('StrS','LoadStoreImm32',False),
    'Float64':('StrD','LoadStoreImm64',False),
    'AnyUncompressedTagged':('Str','LoadStoreImm64',False),
    'UncompressedTaggedPointer':('Str','LoadStoreImm64',False),'UncompressedTaggedSigned':('Str','LoadStoreImm64',False),
    'IndirectPointer':('StrIndirectPointer','LoadStoreImm32','StrIndirectPointer'),
    'SandboxedPointer':('StrEncodeSandboxedPointer','LoadStoreImm64',False),
    'Simd128':('StrQ','NoImmediate',False)}
tagged={'AnyTagged','TaggedPointer','TaggedSigned'}
assert set(mem_names)==set(store_table)|tagged|{'ProtectedPointer','Simd256'}
for name in mem_names:
    for paired in [False,True]:
        expected='std::nullopt'
        if name in store_table:
            op,imm,p=store_table[name]
            if not paired or p: expected=pair(p if paired else op,imm)
        elif name in tagged:
            yes=pair('StrWPair','LoadStoreImm32') if paired else pair('StrCompressTagged','LoadStoreImm32')
            no=pair('StrPair','LoadStoreImm64') if paired else pair('StrCompressTagged','LoadStoreImm64')
            expected='COMPRESS_POINTERS_BOOL ? '+yes+' : '+no
        text+=f'check("store {name} paired={paired}", {expected}, [] {{ return GetStoreOpcodeAndImmediate(MemoryRepresentation::{name}(), {str(paired).lower()}); }});\n'
load_table={
    'Int8':('LdrsbW','LoadStoreImm8','Word32'),'Uint8':('Ldrb','LoadStoreImm8','Word32'),
    'Int16':('LdrshW','LoadStoreImm16','Word32'),'Uint16':('Ldrh','LoadStoreImm16','Word32'),
    'Int32':('LdrW','LoadStoreImm32','Word32'),'Uint32':('LdrW','LoadStoreImm32','Word32'),
    'Int64':('Ldr','LoadStoreImm64','Word64'),'Uint64':('Ldr','LoadStoreImm64','Word64'),
    'Float16':('LdrH','LoadStoreImm16','Float32'),'Float32':('LdrS','LoadStoreImm32','Float32'),
    'Float64':('LdrD','LoadStoreImm64','Float64'),
    'AnyUncompressedTagged':('Ldr','LoadStoreImm64','Tagged'),
    'UncompressedTaggedPointer':('Ldr','LoadStoreImm64','Tagged'),'UncompressedTaggedSigned':('Ldr','LoadStoreImm64','Tagged'),
    'SandboxedPointer':('LdrDecodeSandboxedPointer','LoadStoreImm64',None),'Simd128':('LdrQ','NoImmediate',None)}
assert set(mem_names)==set(load_table)|tagged|{'ProtectedPointer','IndirectPointer','Simd256'}
for name in mem_names:
    for reg in reg_names:
        expected='std::nullopt'
        guard=None
        if name in load_table:
            op,imm,needed=load_table[name];expected=pair(op,imm)
            if needed and reg!=needed:guard='defined(DEBUG)'
        elif name in tagged:
            op='LdrW' if reg=='Compressed' else ('LdrDecompressTaggedSigned' if name=='TaggedSigned' else 'LdrDecompressTagged')
            expected='COMPRESS_POINTERS_BOOL ? '+pair(op,'LoadStoreImm32')+' : '+pair('Ldr','LoadStoreImm64')
            if reg not in ['Compressed','Tagged']:guard='defined(DEBUG) && defined(V8_COMPRESS_POINTERS)'
        elif name=='ProtectedPointer':
            expected='SANDBOX ? std::optional<Result>{'+pair('LdrDecompressProtected','NoImmediate')+'} : std::nullopt'
        if guard: text+='#if '+guard+'\n#define EXPECTED std::nullopt\n#else\n#define EXPECTED '+expected+'\n#endif\n';expected='EXPECTED'
        text+=f'check("load {name} to {reg}", {expected}, [] {{ return GetLoadOpcodeAndImmediate(MemoryRepresentation::{name}(), RegisterRepresentation::{reg}()); }});\n'
        if guard:text+='#undef EXPECTED\n'
legacy_table={'Float16':('LdrH','LoadStoreImm16'),'Float32':('LdrS','LoadStoreImm32'),
    'Float64':('LdrD','LoadStoreImm64'),'Word32':('LdrW','LoadStoreImm32'),
    'Word64':('Ldr','LoadStoreImm64'),'SandboxedPointer':('LdrDecodeSandboxedPointer','LoadStoreImm64'),
    'Simd128':('LdrQ','NoImmediate')}
for name in machine_names:
    for sem in semantic_names:
        expected='std::nullopt'
        if name in legacy_table:expected=pair(*legacy_table[name])
        elif name in ['Bit','Word8','Word16']:
            half=name=='Word16'
            if sem in ['Uint32','Uint64']:op='Ldrh' if half else 'Ldrb'
            elif sem=='Int32':op='LdrshW' if half else 'LdrsbW'
            else:op='Ldrsh' if half else 'Ldrsb'
            expected=pair(op,'LoadStoreImm16' if half else 'LoadStoreImm8')
        elif name in ['CompressedPointer','Compressed']:
            expected='COMPRESS_POINTERS_BOOL ? std::optional<Result>{'+pair('LdrW','LoadStoreImm32')+'} : std::nullopt'
        elif name in ['Tagged','TaggedSigned','TaggedPointer']:
            expected='COMPRESS_POINTERS_BOOL ? '+pair('LdrDecompressTaggedSigned' if name=='TaggedSigned' else 'LdrDecompressTagged','LoadStoreImm32')+' : '+pair('Ldr','LoadStoreImm64')
        elif name=='ProtectedPointer':expected='SANDBOX ? std::optional<Result>{'+pair('LdrDecompressProtected','NoImmediate')+'} : std::nullopt'
        else:assert name in ['None','MapWord','IndirectPointer','Float16RawBits','Simd256'],name
        text+=f'check("legacy {name}/{sem}", {expected}, [] {{ return GetLoadOpcodeAndImmediate(LoadRepresentation{{MachineRepresentation::k{name}, MachineSemantic::k{sem}}}); }});\n'
text+='std::printf("PASS: %u selector cases (%u rejected)\\n", checks, rejected);\n}\n'
(out/'control.cc').write_text(text)
(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n')
(out/'case-counts.json').write_text(json.dumps({'store':len(mem_names)*2,'load':len(mem_names)*len(reg_names),'legacy':len(machine_names)*len(semantic_names),'machine_representations':machine_names},indent=2)+'\n')
shutil.copy2(source/'deps/v8/LICENSE',out/'V8-LICENSE')
runner='''# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import json,subprocess
root=Path('/control');records=[]
for compress,sandbox in [(False,False),(True,False),(True,True)]:
 for mode in ['release','debug']:
  stem=mode+'-c'+str(int(compress))+'-s'+str(int(sandbox))
  flags=['-DV8_COMPRESS_POINTERS'] if compress else []
  flags+=['-DDEBUG'] if mode=='debug' else ['-DNDEBUG']
  commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra','-Wswitch-enum','-Werror=switch-enum','-DSANDBOX='+str(int(sandbox)),*flags,'/control/control.cc','-o','/control/'+stem],['/control/'+stem],['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','/control/'+stem]]
  for step,cmd in zip(['compile','normal','valgrind'],commands):
   with (root/(stem+'-'+step+'.log')).open('x') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
   records.append({'name':stem+'-'+step,'command':cmd,'exit_code':r.returncode})
   (root/'status.json').write_text(json.dumps(records,indent=2)+'\\n')
   r.check_returncode()
'''
(out/'run.py').write_text(runner)
subprocess.run(['docker','run','--rm','--network','none','--user','1019:100','-v',str(out)+':/control',
 'sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414','python3','-B','-W','error','/control/run.py'],check=True)
print('All declared ARM selector inputs checked in release/debug and three supported feature configurations.')
