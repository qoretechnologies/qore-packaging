// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "src/base/virtual-address-space.h"
#include <charconv>
#include <cstdio>
#include <cstring>
#include <system_error>

using Permission = v8::PagePermissions;

int main(int argc, char** argv) {
  if (argc == 3) {
    int values[2] = {};
    for (unsigned i = 0; i < 2; ++i) {
      const char* end = argv[i + 1] + std::strlen(argv[i + 1]);
      const auto parsed = std::from_chars(argv[i + 1], end, values[i]);
      if (parsed.ec != std::errc{} || parsed.ptr != end) {
        return 2;
      }
    }
    std::printf("%d\n", v8::base::IsSubset(static_cast<Permission>(values[0]),
                                         static_cast<Permission>(values[1])));
    return 0;
  }
  if (argc != 1) {
    return 2;
  }
  const struct {
    Permission permission;
    bool read, write, execute;
  } cases[] = {
      {Permission::kNoAccess, false, false, false},
      {Permission::kRead, true, false, false},
      {Permission::kReadWrite, true, true, false},
      {Permission::kReadWriteExecute, true, true, true},
      {Permission::kReadExecute, true, false, true},
  };
  unsigned checks = 0;
  for (unsigned iteration = 0; iteration < 10000; ++iteration) {
    for (const auto& lhs : cases) {
      for (const auto& rhs : cases) {
        const bool expected = (!lhs.read || rhs.read) && (!lhs.write || rhs.write)
            && (!lhs.execute || rhs.execute);
        if (v8::base::IsSubset(lhs.permission, rhs.permission) != expected) {
          std::fprintf(stderr, "Incorrect page permission subset\n");
          return 1;
        }
        ++checks;
      }
    }
  }
  std::printf("%u page permission checks passed\n", checks);
  return 0;
}
