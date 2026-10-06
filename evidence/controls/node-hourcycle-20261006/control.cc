// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Unchanged V8 helper bodies, real ICU strings and original HourCycle enum.
#include <unicode/unistr.h>
#include <array>
#include <cstdio>
#include <cstdlib>
#include <stdexcept>
#include <string>
struct JSDateTimeFormat { enum class HourCycle { kUndefined, kH11, kH12, kH23, kH24 }; };
[[noreturn]] void unreachable() { throw std::logic_error("unreachable hour cycle"); }
#define UNREACHABLE() unreachable()
void require(bool b) { if (!b) { std::abort(); } }

#line 1790 "deps/v8/src/objects/js-date-time-format.cc"
__attribute__((noinline)) icu::UnicodeString ReplaceHourCycleInPattern(icu::UnicodeString pattern,
                                             JSDateTimeFormat::HourCycle hc) {
  char16_t replacement;
  switch (hc) {
    case JSDateTimeFormat::HourCycle::kUndefined:
      return pattern;
    case JSDateTimeFormat::HourCycle::kH11:
      replacement = 'K';
      break;
    case JSDateTimeFormat::HourCycle::kH12:
      replacement = 'h';
      break;
    case JSDateTimeFormat::HourCycle::kH23:
      replacement = 'H';
      break;
    case JSDateTimeFormat::HourCycle::kH24:
      replacement = 'k';
      break;
  }
  bool replace = true;
  icu::UnicodeString result;
  char16_t last = u'\0';
  for (int32_t i = 0; i < pattern.length(); i++) {
    char16_t ch = pattern.charAt(i);
    switch (ch) {
      case '\'':
        replace = !replace;
        result.append(ch);
        break;
      case 'H':
        [[fallthrough]];
      case 'h':
        [[fallthrough]];
      case 'K':
        [[fallthrough]];
      case 'k':
        // If the previous field is a day, add a space before the hour.
        if (replace && last == u'd') {
          result.append(' ');
        }
        result.append(replace ? replacement : ch);
        break;
      default:
        result.append(ch);
        break;
    }
    last = ch;
  }
  return result;
}

#line 2002 "deps/v8/src/objects/js-date-time-format.cc"
__attribute__((noinline)) icu::UnicodeString ReplaceSkeleton(const icu::UnicodeString input,
                                   JSDateTimeFormat::HourCycle hc) {
  icu::UnicodeString result;
  char16_t to;
  switch (hc) {
    case JSDateTimeFormat::HourCycle::kH11:
      to = 'K';
      break;
    case JSDateTimeFormat::HourCycle::kH12:
      to = 'h';
      break;
    case JSDateTimeFormat::HourCycle::kH23:
      to = 'H';
      break;
    case JSDateTimeFormat::HourCycle::kH24:
      to = 'k';
      break;
    case JSDateTimeFormat::HourCycle::kUndefined:
      UNREACHABLE();
  }
  for (int32_t i = 0; i < input.length(); i++) {
    switch (input[i]) {
      // We need to skip 'a', 'b', 'B' here due to
      // https://unicode-org.atlassian.net/browse/ICU-20437
      case 'a':
        [[fallthrough]];
      case 'b':
        [[fallthrough]];
      case 'B':
        // ignore
        break;
      case 'h':
        [[fallthrough]];
      case 'H':
        [[fallthrough]];
      case 'K':
        [[fallthrough]];
      case 'k':
        result += to;
        break;
      default:
        result += input[i];
        break;
    }
  }
  return result;
}

#line 1 "hourcycle-tests.cc"

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
