# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib
import json
import shutil

root = Path('work/node-obs-diagnostic-20261006/node-v24.18.1')
out = Path('work/node-duration-controls-20261007')
out.mkdir()
extracts = []

def take(path, begin, end):
    source = (root / path).read_text()
    start = source.index(begin)
    body = source[start:source.index(end, start)].rstrip()
    extracts.append(dict(file=path, line=source[:start].count('\n') + 1,
                         body=body, sha256=hashlib.sha256(body.encode()).hexdigest()))
    return body

header = 'deps/v8/src/objects/js-duration-format.h'
enums = '\n'.join(take(header, '  enum class ' + name, '\n  };') + '\n  };'
                  for name in ('Display', 'Style', 'FieldStyle'))
source = 'deps/v8/src/objects/js-duration-format.cc'
types = take(source, 'enum class Unit {', '\nconst std::initializer_list<const char*>')
helper = take(source, 'Maybe<DurationUnitOptions> GetDurationUnitOptions(', '\nJSDurationFormat::Separator GetSeparator')
macro = take('deps/v8/src/execution/isolate.h', '#define MAYBE_ASSIGN_RETURN_ON_EXCEPTION_VALUE', '\n#define MAYBE_ASSIGN_RETURN_FAILURE_ON_EXCEPTION')
unit_macro = take(source, '#define CALL_GET_DURATION_UNIT_OPTIONS', '\n  // #table-durationformat')
calls = take(source, '  CALL_GET_DURATION_UNIT_OPTIONS(kYears,', '\n  // [[WeeksStyle]]')
prefix = r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Unchanged option helper and assignment macros; actual V8 Maybe<T> header.
#include <array>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>
#include "v8-maybe.h"
using v8::Maybe; using v8::Just; using v8::Nothing;
void require(bool value) { if (!value) { std::abort(); } }
#define DCHECK(x) require(x)
#define UNREACHABLE() std::abort()
struct JSDurationFormat {
'''+enums+r'''
};
using DirectResult = std::array<unsigned, 4>;
template<class T> using DirectHandle = T*;
struct JSReceiver { std::array<int,4> values; };
struct Isolate {
 unsigned calls=0, fault=0; bool exception=false;
 bool has_exception() const { return exception; }
};
#define THROW_NEW_ERROR_RETURN_VALUE(isolate,error,value) do { (isolate)->exception=true; return value; } while(false)
template<class T> __attribute__((noinline)) Maybe<T> GetStringOption(
 Isolate* isolate, DirectHandle<JSReceiver> options, const char* property,
 const char*, const std::vector<const char*>& names, const std::vector<T>& values, T fallback) {
 ++isolate->calls;
 if(isolate->calls==isolate->fault) {isolate->exception=true;return Nothing<T>();}
 require(names.size()==values.size());
 unsigned field=std::strncmp(property,"months",6)==0?2:0;
 if(std::strstr(property,"Display")) {++field;}
 int index=options->values[field];
 if(index<0) {return Just(fallback);}
 if(static_cast<unsigned>(index)>=values.size()) {isolate->exception=true;return Nothing<T>();}
 return Just(values[index]);
}
'''+types+'\n'+macro+'\n'+helper+r'''
__attribute__((noinline)) Maybe<DirectResult> BuildTwo(Isolate* isolate, JSReceiver* options, JSDurationFormat::Style style) {
 using FieldStyle=JSDurationFormat::FieldStyle;
 const std::vector<const char*> kLongShortNarrowStrings{"long","short","narrow"};
 const std::vector<FieldStyle> kLongShortNarrowEnums{FieldStyle::kLong,FieldStyle::kShort,FieldStyle::kNarrow};
 DurationUnitOptions years_option;
 DurationUnitOptions months_option;
'''
# The only adaptation in the calling macro is its enclosing return type.
unit_macro = unit_macro.replace('DirectHandle<JSDurationFormat>()', 'Nothing<DirectResult>()')
code = prefix + unit_macro + '\n' + calls + r'''
#undef CALL_GET_DURATION_UNIT_OPTIONS
 return Just(DirectResult{static_cast<unsigned>(years_option.style), static_cast<unsigned>(years_option.display),
                          static_cast<unsigned>(months_option.style), static_cast<unsigned>(months_option.display)});
}
int main() {
 unsigned checks=0;
 for(unsigned repeat=0;repeat<100;++repeat) {
  for(auto base:{JSDurationFormat::Style::kLong,JSDurationFormat::Style::kShort,JSDurationFormat::Style::kNarrow,JSDurationFormat::Style::kDigital}) {
   for(int ys=-1;ys<3;++ys) {for(int yd=-1;yd<2;++yd) {
    for(int ms=-1;ms<3;++ms) {for(int md=-1;md<2;++md) {
     JSReceiver options{{ys,yd,ms,md}};
     for(unsigned fault=0;fault<=4;++fault) {
      Isolate isolate;isolate.fault=fault;
      DirectResult result{99,99,99,99};
      bool ok=BuildTwo(&isolate,&options,base).To(&result);
      require(ok==(fault==0));require(isolate.exception==(fault!=0));
      require(isolate.calls==(fault?fault:4));
      if(fault) {require(result==DirectResult({99,99,99,99}));} else {
       unsigned default_style=base==JSDurationFormat::Style::kDigital?1:static_cast<unsigned>(base);
       DirectResult expected{ys<0?default_style:static_cast<unsigned>(ys),
                             yd<0?static_cast<unsigned>(ys>=0):static_cast<unsigned>(yd),
                             ms<0?default_style:static_cast<unsigned>(ms),
                             md<0?static_cast<unsigned>(ms>=0):static_cast<unsigned>(md)};
       require(result==expected);
      }
      ++checks;
     }
    }}
   }}
  }
  for(unsigned field=0;field<4;++field) {
   JSReceiver options{{-1,-1,-1,-1}};options.values[field]=99;
   Isolate isolate;DirectResult result{99,99,99,99};
   require(!BuildTwo(&isolate,&options,JSDurationFormat::Style::kShort).To(&result));
   require(isolate.exception);require(isolate.calls==field+1);require(result==DirectResult({99,99,99,99}));++checks;
  }
 }
 std::printf("PASS: %u duration option and exceptional-return checks\n",checks);
}
'''
(out / 'control.cc').write_text(code)
(out / 'source-extracts.json').write_text(json.dumps(extracts, indent=2) + '\n')
shutil.copy2(root / 'deps/v8/LICENSE', out / 'V8-LICENSE')
runner = Path('work/node-object-dispatch-controls-20261007/run.py').read_text().replace(
    'flags=[]', "flags=['-I/source/deps/v8/include']")
(out / 'run.py').write_text(runner)
