// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
  enum class Display {
    kAuto,
    kAlways,

    kMax = kAlways
  };
  enum class Style {
    kLong,
    kShort,
    kNarrow,
    kDigital,

    kMax = kDigital
  };
  enum class FieldStyle {
    kLong,
    kShort,
    kNarrow,
    kNumeric,
    k2Digit,
    kFractional,
    kUndefined,

    kStyle3Max = kNarrow,
    kStyle4Max = kFractional,
    kStyle5Max = k2Digit,
  };
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
enum class Unit {
  kYears,
  kMonths,
  kWeeks,
  kDays,
  kHours,
  kMinutes,
  kSeconds,
  kMilliseconds,
  kMicroseconds,
  kNanoseconds
};
struct DurationUnitOptions {
  JSDurationFormat::FieldStyle style;
  JSDurationFormat::Display display;
};
#define MAYBE_ASSIGN_RETURN_ON_EXCEPTION_VALUE(isolate, dst, call, value) \
  do {                                                                    \
    if (!(call).To(&dst)) {                                               \
      DCHECK((isolate)->has_exception());                                 \
      return value;                                                       \
    }                                                                     \
  } while (false)
Maybe<DurationUnitOptions> GetDurationUnitOptions(
    Isolate* isolate, Unit unit, const char* unit_string,
    const char* display_field, DirectHandle<JSReceiver> options,
    JSDurationFormat::Style base_style,
    const std::vector<const char*>& value_strings,
    const std::vector<JSDurationFormat::FieldStyle>& value_enums,
    JSDurationFormat::FieldStyle digital_base,
    JSDurationFormat::FieldStyle prev_style) {
  const char* method_name = "Intl.DurationFormat";
  JSDurationFormat::FieldStyle style;
  // 1. Let style be ? GetOption(options, unit, "string", stylesList,
  // undefined).
  MAYBE_ASSIGN_RETURN_ON_EXCEPTION_VALUE(
      isolate, style,
      GetStringOption<JSDurationFormat::FieldStyle>(
          isolate, options, unit_string, method_name, value_strings,
          value_enums, JSDurationFormat::FieldStyle::kUndefined),
      Nothing<DurationUnitOptions>());

  // 2. Let displayDefault be "always".
  JSDurationFormat::Display display_default =
      JSDurationFormat::Display::kAlways;
  // 3. If style is undefined, then
  if (style == JSDurationFormat::FieldStyle::kUndefined) {
    // a. If baseStyle is "digital", then
    if (base_style == JSDurationFormat::Style::kDigital) {
      // i. If unit is not one of "hours", "minutes", or "seconds", then
      if (unit != Unit::kHours && unit != Unit::kMinutes &&
          unit != Unit::kSeconds) {
        // a. Set displayDefault to "auto".
        display_default = JSDurationFormat::Display::kAuto;
      }
      // ii. Set style to digitalBase.
      style = digital_base;
      // b. Else
    } else {
      // i. if prevStyle is "fractional", "numeric", or "2-digit", then
      if (prev_style == JSDurationFormat::FieldStyle::kFractional ||
          prev_style == JSDurationFormat::FieldStyle::kNumeric ||
          prev_style == JSDurationFormat::FieldStyle::k2Digit) {
        // 1. If unit is not one of "minutes" or "seconds", then
        if (unit != Unit::kMinutes && unit != Unit::kSeconds) {
          // a. Set displayDefault to "auto".
          display_default = JSDurationFormat::Display::kAuto;
        }
        // 2. Set style to "numeric".
        style = JSDurationFormat::FieldStyle::kNumeric;
        // iii. Else,
      } else {
        // 1. Set displayDefault to "auto".
        display_default = JSDurationFormat::Display::kAuto;
        // 2. Set style to baseStyle.
        switch (base_style) {
          case JSDurationFormat::Style::kLong:
            style = JSDurationFormat::FieldStyle::kLong;
            break;
          case JSDurationFormat::Style::kShort:
            style = JSDurationFormat::FieldStyle::kShort;
            break;
          case JSDurationFormat::Style::kNarrow:
            style = JSDurationFormat::FieldStyle::kNarrow;
            break;
          default:
            UNREACHABLE();
        }
      }
    }
  }
  // 4. If style is "numeric", then
  if (style == JSDurationFormat::FieldStyle::kNumeric) {
    // a. If unit is one of "milliseconds", "microseconds", or "nanoseconds",
    // then
    if (unit == Unit::kMilliseconds || unit == Unit::kMicroseconds ||
        unit == Unit::kNanoseconds) {
      // i. Set style to "fractional".
      style = JSDurationFormat::FieldStyle::kFractional;
      // ii. Set displayDefault to "auto".
      display_default = JSDurationFormat::Display::kAuto;
    }
  }
  // 5. Let displayField be the string-concatenation of unit and "Display".
  // 6. Let display be ? GetOption(options, displayField, "string", « "auto",
  // "always" », displayDefault).
  JSDurationFormat::Display display;
  MAYBE_ASSIGN_RETURN_ON_EXCEPTION_VALUE(
      isolate, display,
      GetStringOption<JSDurationFormat::Display>(
          isolate, options, display_field, method_name, {"auto", "always"},
          {JSDurationFormat::Display::kAuto,
           JSDurationFormat::Display::kAlways},
          display_default),
      Nothing<DurationUnitOptions>());
  // 7. If display is "always" and style is "fractional", then
  if (display == JSDurationFormat::Display::kAlways &&
      style == JSDurationFormat::FieldStyle::kFractional) {
    // a. Throw a RangeError exception.
    THROW_NEW_ERROR_RETURN_VALUE(
        isolate,
        NewRangeError(MessageTemplate::kInvalid,
                      isolate->factory()->object_string(), options),
        Nothing<DurationUnitOptions>());
  }
  // 8. If prevStyle is "fractional", then
  if (prev_style == JSDurationFormat::FieldStyle::kFractional) {
    // a. If style is not "fractional", then
    if (style != JSDurationFormat::FieldStyle::kFractional) {
      // i. Throw a RangeError exception.
      THROW_NEW_ERROR_RETURN_VALUE(
          isolate,
          NewRangeError(MessageTemplate::kInvalid,
                        isolate->factory()->object_string(), options),
          Nothing<DurationUnitOptions>());
    }
  }
  // 7. If prevStyle is "numeric" or "2-digit", then
  if (prev_style == JSDurationFormat::FieldStyle::kNumeric ||
      prev_style == JSDurationFormat::FieldStyle::k2Digit) {
    // a. If style is not "fractional", "numeric" or "2-digit", then
    if (style != JSDurationFormat::FieldStyle::kFractional &&
        style != JSDurationFormat::FieldStyle::kNumeric &&
        style != JSDurationFormat::FieldStyle::k2Digit) {
      // i. Throw a RangeError exception.
      THROW_NEW_ERROR_RETURN_VALUE(
          isolate,
          NewRangeError(MessageTemplate::kInvalid,
                        isolate->factory()->object_string(), options),
          Nothing<DurationUnitOptions>());
    }
    // b. If unit is "minutes" or "seconds", then
    if (unit == Unit::kMinutes || unit == Unit::kSeconds) {
      // i. Set style to "2-digit".
      style = JSDurationFormat::FieldStyle::k2Digit;
    }
  }
  // 8. Return the Record { [[Style]]: style, [[Display]]: display }.
  return Just(DurationUnitOptions({style, display}));
}
__attribute__((noinline)) Maybe<DirectResult> BuildTwo(Isolate* isolate, JSReceiver* options, JSDurationFormat::Style style) {
 using FieldStyle=JSDurationFormat::FieldStyle;
 const std::vector<const char*> kLongShortNarrowStrings{"long","short","narrow"};
 const std::vector<FieldStyle> kLongShortNarrowEnums{FieldStyle::kLong,FieldStyle::kShort,FieldStyle::kNarrow};
 DurationUnitOptions years_option;
 DurationUnitOptions months_option;
#define CALL_GET_DURATION_UNIT_OPTIONS(unit, property, strings, enums,         \
                                       digital_base, prev_style)               \
  MAYBE_ASSIGN_RETURN_ON_EXCEPTION_VALUE(                                      \
      isolate, property##_option,                                              \
      GetDurationUnitOptions(                                                  \
          isolate, Unit::unit, #property, #property "Display", options, style, \
          strings, enums, JSDurationFormat::FieldStyle::digital_base,          \
          prev_style),                                                         \
      Nothing<DirectResult>());
  CALL_GET_DURATION_UNIT_OPTIONS(kYears, years, kLongShortNarrowStrings,
                                 kLongShortNarrowEnums, kShort,
                                 FieldStyle::kUndefined)
  // [[MonthsStyle]] [[MonthsDisplay]] "months" « "long",
  // "short", "narrow" » "short"
  CALL_GET_DURATION_UNIT_OPTIONS(kMonths, months, kLongShortNarrowStrings,
                                 kLongShortNarrowEnums, kShort,
                                 years_option.style)
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
