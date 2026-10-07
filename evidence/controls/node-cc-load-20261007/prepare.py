# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib, json

root=Path('work/node-obs-diagnostic-20261006/node-v24.18.1')
out=Path('work/node-cc-load-control-20261007');out.mkdir()
path='deps/v8/src/torque/cc-generator.cc'
source=(root/path).read_text();start=source.index('      const char* load;',source.index('This code replicates the way we load the field'))
end=source.index('    }\n  } else {',start)
body=source[start:end]
(out/'source-extracts.json').write_text(json.dumps({'file':path,'line':source[:start].count('\n')+1,
    'body':body,'sha256':hashlib.sha256(body.encode()).hexdigest()},indent=2)+'\n')
(out/'control.cc').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <cstdio>
#include <cstdlib>
#include <sstream>
#include <stdexcept>
#include <string>
enum class FieldSynchronization { kNone, kRelaxed, kAcquireRelease };
struct Instruction { FieldSynchronization synchronization; };
[[noreturn]] void ReportError(const char* text) { throw std::runtime_error(text); }
void require(bool result) { if (!result) { std::abort(); } }
class Generator {
 public:
  std::ostringstream output;
  std::ostream& out() { return output; }
  void Generate(Instruction instruction, const std::string& object,
                const std::string& result_type, const std::string& offset) {
'''+body+r'''
  }
};
int main() {
  size_t checks=0;
  for (unsigned repeat=0; repeat<10000; ++repeat) {
    for (const char* object : {"o", "object_17", "parent->field"}) {
      for (const char* type : {"int32_t", "uint64_t", "Address"}) {
        for (const char* offset : {"0", "4", "(base + index * 8)"}) {
          for (auto mode : {FieldSynchronization::kNone, FieldSynchronization::kRelaxed,
                            FieldSynchronization::kAcquireRelease}) {
            Generator generator;
            if (mode == FieldSynchronization::kAcquireRelease) {
              bool rejected=false;
              try { generator.Generate({mode},object,type,offset); }
              catch (const std::runtime_error& error) {
                require(std::string(error.what())=="Torque doesn't support @cppAcquireLoad on untagged data");
                rejected=true;
              }
              require(rejected && generator.output.str().empty());
            } else {
              generator.Generate({mode},object,type,offset);
              std::string expected="("+std::string(object)+")->"+
                (mode==FieldSynchronization::kNone?"ReadField":"Relaxed_ReadField")+
                "<"+type+">("+offset+");\n";
              require(generator.output.str()==expected);
            }
            ++checks;
          }
        }
      }
    }
  }
  std::printf("PASS: %zu actual C++ load-dispatch branch checks\n",checks);
}
''')
(out/'run.py').write_text('''# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import subprocess,json
out=Path('/control');records=[]
for mode in ('release','debug'):
 commands=[('compile',['g++','-std=c++20','-O3' if mode=='release' else '-O2','-g','-Wall','-Wextra','-Wmaybe-uninitialized','-Werror=return-type',str(out/'control.cc'),'-o',str(out/mode)]),('normal',[str(out/mode)]),('memory',['valgrind','--error-exitcode=99','--leak-check=full','--show-leak-kinds=all','--errors-for-leak-kinds=all','--log-file='+str(out/(mode+'-valgrind.log')),str(out/mode)])]
 for label,command in commands:
  with (out/(mode+'-'+label+'.log')).open('w') as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
  records.append(dict(mode=mode,label=label,command=command,exit_code=r.returncode));(out/'status.json').write_text(json.dumps(records,indent=2)+'\\n');r.check_returncode()
print('Four control runs complete.')
''')
print('Prepared unchanged Torque C++ load branch and all declared synchronization modes.')
