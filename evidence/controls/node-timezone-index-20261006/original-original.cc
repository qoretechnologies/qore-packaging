// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
struct JSTemporalTimeZone { static constexpr int32_t kUTCTimeZoneIndex = 0; };
struct Intl { static std::string TimeZoneIdFromIndex(int32_t index); };
std::string Intl::TimeZoneIdFromIndex(int32_t index) {
  if (index == JSTemporalTimeZone::kUTCTimeZoneIndex) {
    return "UTC";
  }
  std::unique_ptr<icu::StringEnumeration> enumeration(
      icu::TimeZone::createEnumeration());
  int32_t curr = 0;
  const char* id;

  UErrorCode status = U_ZERO_ERROR;
  while (U_SUCCESS(status) && curr < index &&
         ((id = enumeration->next(nullptr, status)) != nullptr)) {
    CHECK(U_SUCCESS(status));
    curr++;
  }
  CHECK(U_SUCCESS(status));
  CHECK(id != nullptr);
  return id;
}

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
