# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess

root = Path.cwd()
source = root / 'results/leap-nodejs24-canonical-final-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1'
out = root / 'work/node-arm-lane-control-20261008'
out.mkdir()
extracts = []
def take(file, begin, end, after=''):
    text = (source / file).read_text()
    a = text.index(begin, text.index(after) if after else 0)
    b = text.index(end, a) + len(end)
    body = text[a:b]
    extracts.append({'file': file, 'line': text[:a].count('\n') + 1, 'text': body,
                     'sha256': hashlib.sha256(body.encode()).hexdigest()})
    return body
machine = take('deps/v8/src/codegen/machine-type.h', 'enum class MachineRepresentation', '\n};')
ops = 'deps/v8/src/compiler/turboshaft/operations.h'
kind = take(ops, '  enum class Kind : uint8_t {', '\n  };', 'struct Simd128ExtractLaneOp :')
body = take(ops, '  static MachineRepresentation element_rep(Kind kind)', '\n  }', 'struct Simd128ExtractLaneOp :')
expected = {'I8x16S': 'Word8', 'I8x16U': 'Word8', 'I16x8S': 'Word16', 'I16x8U': 'Word16',
            'I32x4': 'Word32', 'I64x2': 'Word64', 'F16x8': 'Float32', 'F32x4': 'Float32', 'F64x2': 'Float64'}
assert re.findall(r'\bk(\w+),', kind) == list(expected)
text = '''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// V8 declarations and method below are unchanged BSD-licensed source extracts.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <utility>
'''+machine+'\nstruct Simd128ExtractLaneOp {\n'+kind+'\n'+body+'\n};\n'
text += '''__attribute__((noinline)) MachineRepresentation invoke(Simd128ExtractLaneOp::Kind kind) {
  return Simd128ExtractLaneOp::element_rep(kind);
}
int main() {
  using K = Simd128ExtractLaneOp::Kind;
  using M = MachineRepresentation;
  const std::array cases{
'''+',\n'.join(f'    std::pair{{K::k{name}, M::k{value}}}' for name, value in expected.items())+'''
  };
  unsigned checks = 0;
  for (const auto& [kind, expected] : cases) {
    if (invoke(kind) != expected) {
      std::fprintf(stderr, "FAIL: kind %u\\n", static_cast<unsigned>(kind));
      return 1;
    }
    ++checks;
  }
  std::printf("PASS: %u declared SIMD lane kinds map to their correct machine representations\\n", checks);
}
'''
(out / 'control.cc').write_text(text)
(out / 'source-extracts.json').write_text(json.dumps(extracts, indent=2)+'\n')
shutil.copy2(source / 'deps/v8/LICENSE', out / 'V8-LICENSE')
runner = '''from pathlib import Path
import json,subprocess
root=Path('/control');records=[]
for mode in ('release','debug'):
 commands=[['g++','-std=c++20','-O2','-g','-Wall','-Wextra']+(['-DNDEBUG'] if mode=='release' else ['-DDEBUG'])+['/control/control.cc','-o','/control/'+mode],['/control/'+mode],['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','/control/'+mode]]
 for name,command in zip(('compile','normal','valgrind'),commands):
  with (root/(mode+'-'+name+'.log')).open('x') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
  records.append({'name':mode+'-'+name,'command':command,'exit_code':r.returncode});(root/'status.json').write_text(json.dumps(records,indent=2)+'\\n');r.check_returncode()
'''
(out / 'run.py').write_text('# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT\n'+runner)
cmd = ['docker','run','--rm','--network','none','--user','1019:100','-v',str(out)+':/control',
       'sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414',
       'python3','-B','-W','error','/control/run.py']
subprocess.run(cmd,check=True)
print('All nine unchanged SIMD lane-dispatch branches pass in both modes and under Valgrind.')
