#!/usr/bin/python3
# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
"""Test V8's packaged timezone lookup against real ICU and invalid boundaries."""
import argparse
from pathlib import Path
import shlex
import signal
import subprocess

HEADER = r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Verbatim V8 lookup with the real ICU enumeration and matching UTC constant.
#include <charconv>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <memory>
#include <string>
#include <system_error>
#include <vector>
#include <unicode/timezone.h>
#include <unicode/strenum.h>
#include <unicode/uclean.h>
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr,"CHECK failed: %s\n",#x); std::abort(); } } while (false)
#define CHECK_GT(a,b) CHECK((a) > (b))
struct JSTemporalTimeZone { static constexpr int32_t kUTCTimeZoneIndex = 0; };
struct Intl { static std::string TimeZoneIdFromIndex(int32_t index); };
'''
TESTS = r'''
int main(int argc,char** argv) {
 if(argc==2) {
  int32_t index; const char* end=argv[1]+std::strlen(argv[1]);auto result=std::from_chars(argv[1],end,index);
  if(result.ec!=std::errc{} || result.ptr!=end) { return 2; }
  auto id=Intl::TimeZoneIdFromIndex(index);std::printf("Lookup(%d): %s\n",index,id.c_str());u_cleanup();return 0;
 }
 if(argc!=1) { return 2; }
 unsigned checks=0;
 {
  std::vector<std::string> ids;
  { std::unique_ptr<icu::StringEnumeration> e(icu::TimeZone::createEnumeration());CHECK(e);UErrorCode status=U_ZERO_ERROR;
    while(const char* id=e->next(nullptr,status)) { CHECK(U_SUCCESS(status));ids.emplace_back(id); }
    CHECK(U_SUCCESS(status)); }
  CHECK(!ids.empty());
  for(unsigned repeat=0;repeat<8;++repeat) {
   CHECK(Intl::TimeZoneIdFromIndex(0)=="UTC");++checks;
   for(size_t i=0;i<ids.size();++i) { CHECK(Intl::TimeZoneIdFromIndex(static_cast<int32_t>(i+1))==ids[i]);++checks; }
  }
  std::printf("%u complete-enumeration and UTC lookup checks passed; zone count=%zu\n",checks,ids.size());
 }
 u_cleanup();return 0;
}
'''

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cxxflags', default='-O2 -g')
    args = parser.parse_args()
    source = (args.source / 'deps/v8/src/objects/intl-objects.cc').read_text()
    begin = source.index('std::string Intl::TimeZoneIdFromIndex(')
    end = source.index('\nint32_t Intl::GetTimeZoneIndex', begin)
    # The adapter's UTC value must agree with V8's actual stored representation.
    temporal = (args.source / 'deps/v8/src/objects/js-temporal-objects.h').read_text()
    if 'static constexpr int32_t kUTCTimeZoneIndex = 0;' not in temporal:
        raise RuntimeError('Review the timezone UTC adapter for this V8 version')
    args.output.mkdir(parents=True, exist_ok=True)
    unit = args.output / 'timezone-index.cc'
    unit.write_text(HEADER + source[begin:end] + TESTS)
    binary = (args.output / 'timezone-index').resolve()
    icu = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs', 'icu-i18n', 'icu-uc'], text=True))
    subprocess.run(['g++', '-std=c++20', *shlex.split(args.cxxflags), '-Wall', '-Wextra', '-Werror', str(unit), *icu, '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
    # The standalone adapter uses abort for V8 CHECK. No invalid index may
    # proceed to strlen through an indeterminate pointer or return a string.
    for index in ('-1', '-2', '-2147483648', '2147483647'):
        result = subprocess.run([str(binary), index], capture_output=True, text=True)
        expected = '(index) > (0)' if index.startswith('-') else 'id != nullptr'
        if result.returncode != -signal.SIGABRT or 'CHECK failed: ' + expected not in result.stderr:
            raise AssertionError((index, result.returncode, result.stdout, result.stderr))
        print('Invalid timezone index rejected:', index)

if __name__ == '__main__':
    main()
