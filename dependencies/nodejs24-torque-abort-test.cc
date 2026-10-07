// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "src/torque/instructions.h"
#include <charconv>
#include <cstdio>
#include <cstring>
#include <system_error>

using Allocator = v8::internal::torque::AbortInstruction;
using Status = Allocator::Kind;

int main(int argc, char** argv) {
  if (argc == 2) {
    int value = 0;
    const char* end = argv[1] + std::strlen(argv[1]);
    const auto parsed = std::from_chars(argv[1], end, value);
    if (parsed.ec != std::errc{} || parsed.ptr != end) {
      return 2;
    }
    // A scoped enum has a fixed underlying int type: every int is representable.
    std::puts(Allocator::KindToString(static_cast<Status>(value)));
    return 0;
  }
  if (argc != 1) {
    return 2;
  }
  const struct {
    Status status;
    const char* expected;
  } cases[] = {
      {Status::kDebugBreak, "kDebugBreak"},
      {Status::kUnreachable, "kUnreachable"},
      {Status::kAssertionFailure, "kAssertionFailure"},
  };
  unsigned checks = 0;
  for (unsigned iteration = 0; iteration < 10000; ++iteration) {
    for (const auto& item : cases) {
      const char* actual = Allocator::KindToString(item.status);
      if (actual == nullptr || std::strcmp(actual, item.expected) != 0) {
        std::fprintf(stderr, "Incorrect Torque abort kind description\n");
        return 1;
      }
      ++checks;
    }
  }
  std::printf("%u Torque abort kind checks passed\n", checks);
  return 0;
}
