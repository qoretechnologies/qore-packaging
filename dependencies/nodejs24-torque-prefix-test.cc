// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#define main torque_compiler_main
#include "src/torque/torque.cc"
#undef main
#include <charconv>
#include <cstdio>
#include <cstring>
#include <system_error>
using Kind = v8::internal::torque::TorqueMessage::Kind;
using v8::internal::torque::ErrorPrefixFor;
int main(int argc, char** argv) {
  if (argc == 2) {
    int value = 0;
    const char* end = argv[1] + std::strlen(argv[1]);
    const auto parsed = std::from_chars(argv[1], end, value);
    if (parsed.ec != std::errc{} || parsed.ptr != end) { return 2; }
    std::puts(ErrorPrefixFor(static_cast<Kind>(value)).c_str());
    return 0;
  }
  if (argc != 1) { return 2; }
  for (unsigned iteration = 0; iteration < 10000; ++iteration) {
    if (ErrorPrefixFor(Kind::kError) != "Torque Error"
        || ErrorPrefixFor(Kind::kLint) != "Lint error") {
      std::fprintf(stderr, "Incorrect diagnostic prefix\n");
      return 1;
    }
  }
  std::puts("20000 Torque diagnostic prefix checks passed");
  return 0;
}
