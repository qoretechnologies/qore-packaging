// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "src/libplatform/default-platform.h"
#include <climits>
#include <cstdio>
#include <cstdlib>
using Platform = v8::platform::DefaultPlatform;
using Priority = v8::base::Thread::Priority;
// Explicit instantiation permits private member access without altering headers.
struct PriorityAccess {
  using type = Priority (Platform::*)(int) const;
  friend type method(PriorityAccess);
};
template<typename Tag, typename Tag::type Member> struct Access {
  friend typename Tag::type method(Tag) { return Member; }
};
template struct Access<PriorityAccess, &Platform::priority_from_index>;
int main(int argc, char** argv) {
  auto function = method(PriorityAccess{});
  Platform enabled(0, v8::platform::IdleTaskSupport::kDisabled, {}, v8::platform::PriorityMode::kApply);
  if (argc == 2) {
    (enabled.*function)(std::atoi(argv[1]));
    return 99;
  }
  Platform disabled;
  int count = 0;
  for (int i = 0; i < 10000; ++i) {
    for (const auto& item : {std::pair<int, Priority>{static_cast<int>(v8::TaskPriority::kBestEffort), Priority::kBestEffort},
                           {static_cast<int>(v8::TaskPriority::kUserVisible), Priority::kUserVisible},
                           {static_cast<int>(v8::TaskPriority::kUserBlocking), Priority::kUserBlocking}}) {
      if ((enabled.*function)(item.first) != item.second) { return 1; }
      if ((disabled.*function)(item.first) != Priority::kDefault) { return 2; }
      count += 2;
    }
    for (int index : {-1, INT_MIN, INT_MAX}) {
      if ((disabled.*function)(index) != Priority::kDefault) { return 3; }
      ++count;
    }
  }
  std::printf("%d priority mapping checks passed\n", count);
  return 0;
}
