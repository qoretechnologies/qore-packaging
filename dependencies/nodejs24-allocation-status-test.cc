// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "src/base/bounded-page-allocator.h"
#include <charconv>
#include <cstdio>
#include <cstring>
#include <system_error>

using Allocator = v8::base::BoundedPageAllocator;
using Status = Allocator::AllocationStatus;

int main(int argc, char** argv) {
  if (argc == 2) {
    int value = 0;
    const char* end = argv[1] + std::strlen(argv[1]);
    const auto parsed = std::from_chars(argv[1], end, value);
    if (parsed.ec != std::errc{} || parsed.ptr != end) {
      return 2;
    }
    // A scoped enum has a fixed underlying int type: every int is representable.
    std::puts(Allocator::AllocationStatusToString(static_cast<Status>(value)));
    return 0;
  }
  if (argc != 1) {
    return 2;
  }
  const struct {
    Status status;
    const char* expected;
  } cases[] = {
      {Status::kSuccess, "Success"},
      {Status::kFailedToCommit, "Failed to commit"},
      {Status::kRanOutOfReservation, "Ran out of reservation"},
      {Status::kHintedAddressTakenOrNotFound, "Hinted address was taken or not found"},
  };
  unsigned checks = 0;
  for (unsigned iteration = 0; iteration < 10000; ++iteration) {
    for (const auto& item : cases) {
      const char* actual = Allocator::AllocationStatusToString(item.status);
      if (actual == nullptr || std::strcmp(actual, item.expected) != 0) {
        std::fprintf(stderr, "Incorrect allocation status description\n");
        return 1;
      }
      ++checks;
    }
  }
  std::printf("%u allocation status checks passed\n", checks);
  return 0;
}
