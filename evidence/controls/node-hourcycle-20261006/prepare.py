# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil,subprocess
root=Path.cwd();src=root/'work/node-obs-diagnostic-20261006/node-v24.18.1';out=root/'work/node-hourcycle-control-20261006';out.mkdir()
p='deps/v8/src/objects/js-date-time-format.cc';s=(src/p).read_text();extracts={}
for name,end in [('ReplaceHourCycleInPattern','std::unique_ptr<icu::SimpleDateFormat> CreateICUDateFormat('),('ReplaceSkeleton','std::unique_ptr<icu::SimpleDateFormat> DateTimeStylePattern(')]:
 a=s.index('icu::UnicodeString '+name+'(');b=s.index(end,a);body=s[a:b].rstrip();extracts[name]={'path':p,'line':s[:a].count('\n')+1,'body':body,'sha256':hashlib.sha256(body.encode()).hexdigest()}
h=(src/'deps/v8/src/objects/js-date-time-format.h').read_text();a=h.index('enum class HourCycle');enum=h[a:h.index(';',a)+1]
header='''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Unchanged V8 helper bodies, real ICU strings and original HourCycle enum.
#include <unicode/unistr.h>
#include <array>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#include <string>
struct JSDateTimeFormat { ENUM };
[[noreturn]] void unreachable() { throw std::logic_error("unreachable hour cycle"); }
#define UNREACHABLE() unreachable()
void require(bool b) { if (!b) { std::abort(); } }
'''.replace('ENUM',enum)
tests=r'''
struct Case { const char16_t* input; const char16_t* expected; };
icu::UnicodeString expected(const char16_t* pattern,char16_t replacement) {
 icu::UnicodeString result(pattern);
 for(int32_t i=0;i<result.length();++i) { if(result[i]==u'@') { result.setCharAt(i,replacement); } }
 return result;
}
int main() {
 using H=JSDateTimeFormat::HourCycle;
 const std::array<H,4> cycles{H::kH11,H::kH12,H::kH23,H::kH24};
 const std::array<char16_t,4> replacements{u'K',u'h',u'H',u'k'};
 const Case patterns[]={
  {u"",u""},{u"HhKk",u"@@@@"},{u"'HhKk' H",u"'HhKk' @"},{u"dH",u"d @"},
  {u"'dH' dH",u"'dH' d @"},{u"HH:mm 'h o''clock' 'X' k",u"@@:mm 'h o''clock' 'X' @"},
  {u"d'H'dk",u"d'H'd @"},{u"''H",u"''@"},{u"d'foo'H",u"d'foo'@"},
  {u"年dH分",u"年d @分"},{u"''dH",u"''d @"},{u"'H",u"'H"},{u"d''H",u"d''@"}
 };
 const Case skeletons[]={{u"",u""},{u"hHkKabBms",u"@@@@ms"},{u"abB",u""},{u"yyyyMMdd",u"yyyyMMdd"},{u"年H分h秒",u"年@分@秒"},{u"HH:mm:ss a",u"@@:mm:ss "},{u"kKBBHH",u"@@@@"}};
 unsigned checks=0,rejections=0;
 for(int repeat=0;repeat<10000;++repeat) {
  for(auto p:patterns) {
   require(ReplaceHourCycleInPattern(icu::UnicodeString(p.input),H::kUndefined)==icu::UnicodeString(p.input));++checks;
   for(size_t i=0;i<cycles.size();++i) { require(ReplaceHourCycleInPattern(icu::UnicodeString(p.input),cycles[i])==expected(p.expected,replacements[i]));++checks; }
  }
  for(auto p:skeletons) {
   for(size_t i=0;i<cycles.size();++i) { require(ReplaceSkeleton(icu::UnicodeString(p.input),cycles[i])==expected(p.expected,replacements[i]));++checks; }
   bool rejected=false;try { ReplaceSkeleton(icu::UnicodeString(p.input),H::kUndefined); } catch(const std::logic_error&) { rejected=true;++rejections; }
   require(rejected);++checks;
  }
 }
 for(int size:{0,1,15,16,31,32,127,128,4096,65536}) {
  icu::UnicodeString input,pattern_expected,skeleton_expected;
  for(int i=0;i<size;++i) { input.append(u'd').append(u'H');pattern_expected.append(u'd').append(u' ').append(u'k');skeleton_expected.append(u'd').append(u'k'); }
  require(ReplaceHourCycleInPattern(input,H::kH24)==pattern_expected);++checks;
  require(ReplaceSkeleton(input,H::kH24)==skeleton_expected);++checks;
 }
 std::printf("PASS: %u ICU pattern/skeleton checks, including %u invalid undefined-skeleton rejections\n",checks,rejections);
}
'''
body=''.join('\n#line '+str(e['line'])+' "'+e['path']+'"\n__attribute__((noinline)) '+e['body']+'\n' for e in extracts.values())
(out/'control.cc').write_text(header+body+'\n#line 1 "hourcycle-tests.cc"\n'+tests)
(out/'source-extracts.json').write_text(json.dumps({'enum':enum,'bodies':extracts,'limitations':'Uses the exact helper bodies and real ICU 77.1 UnicodeString from the compiler image. The full V8 locale/option pipeline is reviewed separately; UNREACHABLE is represented by a throwing noreturn adapter to test its negative branch.'},indent=2)+'\n')
shutil.copy2(src/'deps/v8/LICENSE',out/'V8-LICENSE')
run=Path('work/node-torque-debug-control-20261006/run.py').read_text().replace("['/work/control.cc','-o','/work/control-'+mode]","['/work/control.cc','-licuuc','-licudata','-o','/work/control-'+mode]")
(out/'run.py').write_text(run);cmd=['docker','run','--rm','--init','--network','none','--user','1019:100','-v',str(out)+':/work','sha256:471fb347e0308caa05f79e41ca4813767c6a7a687f03cc823a78b2a8e81a3414','python3','-B','-W','error','/work/run.py'];(out/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
with (out/'run.log').open('x') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
