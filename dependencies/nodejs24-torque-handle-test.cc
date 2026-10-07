// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "src/torque/types.h"
#include <charconv>
#include <cstdio>
#include <cstring>
#include <string>
#include <system_error>
using Type = v8::internal::torque::Type;
using Kind = Type::HandleKind;
int main(int argc, char** argv) {
  if (argc == 2) {
    int value = 0;
    const char* end = argv[1] + std::strlen(argv[1]);
    const auto parsed = std::from_chars(argv[1], end, value);
    if (parsed.ec != std::errc{} || parsed.ptr != end) { return 2; }
    std::puts(Type::GetHandleTypeName(static_cast<Kind>(value), "Object").c_str());
    return 0;
  }
  if (argc != 1) { return 2; }
  const std::string names[] = {"", "Object", "Foo<Bar>", "a::b", "\xc3\xa9", std::string(10000, 'x')};
  unsigned checks = 0;
  for (unsigned iteration = 0; iteration < 10000; ++iteration) {
    for (const auto& name : names) {
      if (Type::GetHandleTypeName(Kind::kIndirect, name) != "Handle<" + name + ">"
          || Type::GetHandleTypeName(Kind::kDirect, name) != "DirectHandle<" + name + ">") {
        std::fprintf(stderr, "Incorrect generated handle name\n");
        return 1;
      }
      checks += 2;
    }
  }
  std::printf("%u Torque handle checks passed\n", checks);
  return 0;
}
