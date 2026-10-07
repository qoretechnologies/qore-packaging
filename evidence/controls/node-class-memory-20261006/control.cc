// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <cstdio>
#include <cstring>
#include <memory>
#include <type_traits>
#include <vector>
#include "src/zone/zone-containers.h"
#include "src/zone/accounting-allocator.h"
#include "src/compiler/backend/instruction.h"
#include "src/heap/heap.h"

namespace i = v8::internal;
namespace c = v8::internal::compiler;
struct ConstEntry {
  const unsigned value;
  const unsigned complement;
  explicit ConstEntry(unsigned n) : value(n), complement(~n) {}
};
static_assert(std::is_trivially_copyable_v<ConstEntry>);
static_assert(!std::is_copy_assignable_v<ConstEntry>);
static_assert(std::is_trivially_copyable_v<c::DeoptimizationEntry>);
static_assert(!std::is_copy_assignable_v<c::DeoptimizationEntry>);
static_assert(std::is_trivially_copyable_v<i::HeapStats>);
static_assert(std::is_trivially_destructible_v<i::HeapStats>);
static_assert(!std::is_trivially_copyable_v<std::unique_ptr<unsigned>>);

static size_t checks = 0;
static void Check(bool condition) {
  ++checks;
  if (!condition) {
    std::fprintf(stderr, "check failed: %zu\n", checks);
    std::abort();
  }
}
// Explicit template instantiation can name private members. These accessors
// exercise the unmodified ZoneVector transfer functions without linking the
// separately hidden V8 arena allocator. The storage belongs to this fixture.
struct ConstCopyTag {
  using Pointer = void (i::ZoneVector<ConstEntry>::*)(ConstEntry*, const ConstEntry*, const ConstEntry*);
  friend Pointer Get(ConstCopyTag);
};
struct DeoptCopyTag {
  using Entry = c::DeoptimizationEntry;
  using Pointer = void (i::ZoneVector<Entry>::*)(Entry*, const Entry*, const Entry*);
  friend Pointer Get(DeoptCopyTag);
};
struct ConstMoveTag {
  using Pointer = void (i::ZoneVector<ConstEntry>::*)(ConstEntry*, ConstEntry*, const ConstEntry*);
  friend Pointer Get(ConstMoveTag);
};
struct OwnedMoveTag {
  using Entry = std::unique_ptr<unsigned>;
  using Pointer = void (i::ZoneVector<Entry>::*)(Entry*, Entry*, const Entry*);
  friend Pointer Get(OwnedMoveTag);
};
template <typename Tag, typename Tag::Pointer P> struct Access {
  friend typename Tag::Pointer Get(Tag) { return P; }
};
template struct Access<ConstCopyTag, &i::ZoneVector<ConstEntry>::CopyToNewStorage>;
template struct Access<DeoptCopyTag, &i::ZoneVector<c::DeoptimizationEntry>::CopyToNewStorage>;
template struct Access<ConstMoveTag, &i::ZoneVector<ConstEntry>::MovingOverwrite>;
template struct Access<OwnedMoveTag, &i::ZoneVector<std::unique_ptr<unsigned>>::MovingOverwrite>;

int main() {
  for (unsigned iteration = 0; iteration < 10; ++iteration) {
    for (unsigned count = 0; count <= 64; ++count) {
      std::vector<ConstEntry> original;
      std::vector<ConstEntry> copied;
      for (unsigned n = 0; n <= count; ++n) {
        original.emplace_back(n + iteration);
        copied.emplace_back(999999);
      }
      i::ZoneVector<ConstEntry> transfers(nullptr);
      (transfers.*Get(ConstCopyTag{}))(copied.data(), original.data(), original.data() + count);
      for (unsigned n = 0; n < count; ++n) {
        Check(copied[n].value == original[n].value);
        Check(copied[n].complement == original[n].complement);
      }
      Check(copied[count].value == 999999);
      if (count > 0) {
        // Overlapping shifts in both directions use the real memmove branch.
        (transfers.*Get(ConstMoveTag{}))(original.data() + 1, original.data(), original.data() + count);
        for (unsigned n = 0; n < count; ++n) {
          Check(original[n + 1].value == n + iteration);
        }
        (transfers.*Get(ConstMoveTag{}))(original.data(), original.data() + 1, original.data() + count + 1);
        for (unsigned n = 0; n < count; ++n) {
          Check(original[n].value == n + iteration);
        }
      }
      std::vector<c::DeoptimizationEntry> deopts;
      std::vector<c::DeoptimizationEntry> deoptCopies;
      for (unsigned n = 0; n <= count; ++n) {
        deopts.emplace_back(nullptr, i::DeoptimizeKind::kEager, i::DeoptimizeReason::kUnknown, n, c::FeedbackSource{});
        deoptCopies.emplace_back(nullptr, i::DeoptimizeKind::kLazy, i::DeoptimizeReason::kUnknown, n, c::FeedbackSource{});
      }
      i::ZoneVector<c::DeoptimizationEntry> deoptTransfers(nullptr);
      (deoptTransfers.*Get(DeoptCopyTag{}))(deoptCopies.data(), deopts.data(), deopts.data() + count);
      for (unsigned n = 0; n < count; ++n) {
        Check(deoptCopies[n].kind() == i::DeoptimizeKind::kEager);
        Check(deoptCopies[n].descriptor() == nullptr);
        Check(deoptCopies[n].reason() == i::DeoptimizeReason::kUnknown);
      }
      Check(deoptCopies[count].kind() == i::DeoptimizeKind::kLazy);
      // Nontrivial ownership must use element-wise move assignment, not memcpy.
      std::vector<std::unique_ptr<unsigned>> owned, moved;
      for (unsigned n = 0; n <= count; ++n) {
        owned.emplace_back(std::make_unique<unsigned>(n));
        moved.emplace_back(std::make_unique<unsigned>(999999));
      }
      i::ZoneVector<std::unique_ptr<unsigned>> ownershipTransfers(nullptr);
      (ownershipTransfers.*Get(OwnedMoveTag{}))(moved.data(), owned.data(), owned.data() + count);
      for (unsigned n = 0; n < count; ++n) {
        Check(!owned[n]);
        Check(*moved[n] == n);
      }
      Check(*moved[count] == 999999);
    }
  }
  for (unsigned iteration = 0; iteration < 1024; ++iteration) {
    struct Guarded { unsigned before = 0x01234567; i::HeapStats stats; unsigned after = 0x89abcdef; } guarded;
    // Identical operation to api.cc's no-isolate fatal-OOM diagnostic.
    std::memset(&guarded.stats, 0xBADC0DE, sizeof(guarded.stats));
    Check(guarded.before == 0x01234567 && guarded.after == 0x89abcdef);
    const auto* data = reinterpret_cast<const unsigned char*>(&guarded.stats);
    for (size_t j = 0; j < sizeof(guarded.stats); ++j) {
      Check(data[j] == 0xde);
    }
  }
  std::printf("%zu class-memory checks passed\n", checks);
}
