# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib, json, shutil
root=Path('work/node-obs-diagnostic-20261006/node-v24.18.1')
out=Path('work/node-lookaround-controls-20261007');out.mkdir();extracts=[]
def take(path,start,end):
 s=(root/path).read_text();a=s.index(start);body=s[a:s.index(end,a)].rstrip()
 extracts.append(dict(file=path,line=s[:a].count('\n')+1,body=body,sha256=hashlib.sha256(body.encode()).hexdigest()));return body
opcode=take('deps/v8/src/regexp/experimental/experimental-bytecode.h','  enum Opcode : int32_t {','\n  struct')
isfilter=take('deps/v8/src/regexp/experimental/experimental-bytecode.h','  static bool IsFilter(', '\n\n  Opcode opcode;')
body=take('deps/v8/src/regexp/experimental/experimental-interpreter.cc','    std::optional<struct Lookaround> lookaround;', '\n\n    // Iniitializes')
source=r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <numeric>
#include <optional>
#include <vector>
void require(bool value) {if(!value) {std::abort();}}
#ifdef DEBUG
#define DCHECK(x) require(x)
#else
#define DCHECK(x) ((void)0)
#endif
struct RegExpLookaround {enum class Type {LOOKBEHIND, LOOKAHEAD};};
struct LookaroundPayload {
 int id=0; RegExpLookaround::Type kind=RegExpLookaround::Type::LOOKBEHIND;
 int index() const {return id;}
 RegExpLookaround::Type type() const {return kind;}
};
struct RegExpInstruction {
'''+opcode+r'''
 Opcode opcode=ACCEPT;
 struct Payload {LookaroundPayload lookaround; int quantifier_id=0;} payload;
'''+isfilter+r'''
};
template<class T> struct ZoneList {
 std::vector<T> values;
 int length() const {return static_cast<int>(values.size());}
 T& operator[](int i) {require(i>=0 && i<length());return values[i];}
 void Add(T value,int) {values.push_back(value);}
 void Set(int i,T value) {require(i>=0 && i<length());values[i]=value;}
};
struct Lookaround {int match_pc; int capture_pc; RegExpLookaround::Type type;};
struct Flags {bool experimental_regexp_engine_capture_group_opt=true;} v8_flags;
struct Interpreter {
 ZoneList<RegExpInstruction> bytecode_;
 ZoneList<Lookaround> lookarounds_;
 bool only_captureless_lookbehinds_=true;
 std::optional<int> filter_groups_pc_;
 int quantifier_count_=0;
 int zone_=0;
 void Scan();
};
__attribute__((noinline)) void Interpreter::Scan() {
'''+body+r'''
}
int main() {
 unsigned checks=0;
 for(unsigned repeat=0;repeat<10;++repeat) {
  for(unsigned count=0;count<=4;++count) {
   std::vector<int> order(count);std::iota(order.begin(),order.end(),0);
   do {
    for(unsigned types=0;types<(1u<<count);++types) {
     for(unsigned captures=0;captures<(1u<<count);++captures) {
      for(bool gaps:{false,true}) {
       Interpreter scan;
       std::vector<Lookaround> expected(count*(gaps?2:1),{-1,-1,RegExpLookaround::Type::LOOKBEHIND});
       auto emit=[&](RegExpInstruction::Opcode opcode) {RegExpInstruction inst;inst.opcode=opcode;scan.bytecode_.values.push_back(inst);};
       bool simple=true;
       emit(RegExpInstruction::SET_REGISTER_TO_CP); // outside a lookaround
       for(int raw:order) {
        int index=gaps?raw*2+1:raw;
        auto type=(types&(1u<<raw))?RegExpLookaround::Type::LOOKAHEAD:RegExpLookaround::Type::LOOKBEHIND;
        int match=scan.bytecode_.length();emit(RegExpInstruction::START_LOOKAROUND);
        scan.bytecode_.values.back().payload.lookaround={index,type};
        emit(RegExpInstruction::CONSUME_RANGE);
        if(captures&(1u<<raw)) {emit(RegExpInstruction::SET_REGISTER_TO_CP);simple=false;}
        if(type==RegExpLookaround::Type::LOOKAHEAD) {simple=false;}
        emit(RegExpInstruction::WRITE_LOOKAROUND_TABLE);
        expected[index]={match,scan.bytecode_.length(),type};
        emit(RegExpInstruction::CONSUME_RANGE);emit(RegExpInstruction::END_LOOKAROUND);
       }
       emit(RegExpInstruction::SET_REGISTER_TO_CP);
       for(int id:{0,5,2,5}) {emit(RegExpInstruction::SET_QUANTIFIER_TO_CLOCK);scan.bytecode_.values.back().payload.quantifier_id=id;}
       int filter=scan.bytecode_.length();emit(RegExpInstruction::FILTER_GROUP);emit(RegExpInstruction::FILTER_CHILD);emit(RegExpInstruction::ACCEPT);
       scan.Scan();
       require(scan.lookarounds_.values.size()==expected.size());
       for(size_t i=0;i<expected.size();++i) {
        const auto& a=scan.lookarounds_.values[i];const auto& e=expected[i];
        require(a.match_pc==e.match_pc && a.capture_pc==e.capture_pc && a.type==e.type);
       }
       require(scan.only_captureless_lookbehinds_==simple && scan.filter_groups_pc_==filter && scan.quantifier_count_==6);++checks;
      }
     }
    }
   } while(std::next_permutation(order.begin(),order.end()));
  }
  Interpreter empty;empty.bytecode_.values.push_back({});empty.Scan();
  require(empty.lookarounds_.length()==0 && !empty.filter_groups_pc_ && empty.quantifier_count_==0 && empty.only_captureless_lookbehinds_);++checks;
 }
 std::printf("PASS: %u lookaround order, capture, gap and boundary checks\n",checks);
}
'''
(out/'control.cc').write_text(source)
(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n')
shutil.copy2(root/'deps/v8/LICENSE',out/'V8-LICENSE')
s=Path('work/node-deopt-scan-controls-20261007/run.py').read_text().replace("flags=['/work/helper.cc']","flags=[]")
(out/'run.py').write_text(s)
(out/'control.js').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert = require('node:assert/strict');
const patterns = ['a', '(?<=a)b', '(?<!a)b', 'a(?=b)', 'a(?!b)',
  '(?=(a+))a', '(?<=(a))b', '(?<=a)(?=b)b', '(?<=(?<=a)b)c',
  '(?=(a(?=b)))ab', '(?!(a))b', '((?<=a)b|c)', '(a+)(?=b)',
  '(?<=ab)c|a(?=bc)', '(?<=a)(b*)(?=c)'];
const inputs=[''];
for(let length=1;length<=5;++length) {
  for(let bits=0;bits<3**length;++bits) {
    let n=bits, s='';for(let i=0;i<length;++i) {s+='abc'[n%3];n=Math.floor(n/3);}inputs.push(s);
  }
}
let checks=0;
for(let repeat=0;repeat<5;++repeat) {
  for(const pattern of patterns) {
    const baseline=new RegExp(pattern), linear=new RegExp(pattern,'l');
    for(const input of inputs) {
      const a=baseline.exec(input), b=linear.exec(input);
      assert.deepStrictEqual(b,a);++checks;
    }
  }
}
for(const pattern of ['(?<=', '(?=)', '[', '(?<(a))', 'a{2,1}']) {
  if(pattern==='(?=)') {assert.deepStrictEqual(new RegExp(pattern,'l').exec(''), /(?=)/.exec(''));}
  else {assert.throws(()=>new RegExp(pattern,'l'), SyntaxError);}
  ++checks;
}
console.log(`PASS: ${checks} actual linear-regexp result, capture and syntax checks`);
''')
print('Prepared unchanged lookaround scan and actual linear-regexp comparisons.')
