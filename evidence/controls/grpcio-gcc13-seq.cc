// Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.
#include "src/core/lib/surface/call_utils.h"
#include "src/core/lib/promise/seq.h"
#include "src/core/lib/promise/activity.h"
#include <cstdio>
#undef NDEBUG
#include <cassert>
using namespace grpc_core;
struct CounterWakeable final : Wakeable {
  int drops = 0;
  int wakes = 0;
  void Wakeup(WakeupMask mask) override { assert(mask == 7); ++wakes; }
  void WakeupAsync(WakeupMask mask) override { Wakeup(mask); }
  void Drop(WakeupMask mask) override { assert(mask == 7); ++drops; }
  std::string ActivityDebugTag(WakeupMask) const override { return "control"; }
};
struct First {
  bool* ready;
  Poll<int> operator()() { if (!*ready) { return Pending{}; } return 19; }
};
struct Last {
  absl::Status status;
  Waker waker;
  bool* ready;
  Poll<Empty> operator()() {
    if (!*ready) { return Pending{}; }
    assert(status.message() == "sequence-owned-status");
    waker.Wakeup();
    return Empty{};
  }
};
int main() {
  int checks = 0;
  for (int round = 0; round < 10000; ++round) {
    for (int stage = 0; stage < 4; ++stage) {
      bool first = false, second = false, last = false;
      int factories = 0;
      CounterWakeable target;
      {
        auto sequence = Seq(First{&first},
            [&second, &factories](int value) {
              assert(value == 19); ++factories;
              return First{&second};
            },
            [&last, &target, &factories](int value) {
              assert(value == 19); ++factories;
              return Last{absl::InternalError("sequence-owned-status"), Waker(&target, 7), &last};
            });
        // Seq can be moved only before polling. These are the same temporary
        // moves made by LogPollBatch in ServerCall::CommitBatch.
        auto moved = LogPollBatch(nullptr, std::move(sequence));
        if (stage == 0) {
          assert(moved().pending());
          assert(factories == 0);
        } else if (stage == 1) {
          first = true;
          assert(moved().pending());
          assert(factories == 1);
        } else {
          first = second = true;
          assert(moved().pending());
          assert(factories == 2);
          if (stage == 3) {
            last = true;
            assert(moved().ready());
          }
        }
      }
      assert(target.drops == (stage == 2 ? 1 : 0));
      assert(target.wakes == (stage == 3 ? 1 : 0));
      ++checks;
    }
    // Exercise the exact inactive WaitForCqEndOp alternative named by GCC:
    // it must never be constructed or destroyed while the earlier step waits.
    bool ready = false;
    auto unstarted = Seq(First{&ready}, [](int) { return [] { return Empty{}; }; }, [] {
      return WaitForCqEndOp(false, nullptr, absl::OkStatus(), nullptr);
    });
    auto moved = LogPollBatch(nullptr, std::move(unstarted));
    assert(moved().pending());
    ++checks;
    // The NotStarted variant holds a real allocated Status, moves through
    // Invalid safely and must release it without touching Started's Waker.
    WaitForCqEndOp completion(false, nullptr, absl::InternalError("owned status for move"), nullptr);
    WaitForCqEndOp transferred(std::move(completion));
    ++checks;
  }
  std::printf("%d sequence state, move, status and wakeable ownership cases passed\n", checks);
}
