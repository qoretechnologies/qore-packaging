// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <cstdio>
#include <vector>
#include "src/compiler/turboshaft/snapshot-table.h"
#include "src/zone/accounting-allocator.h"
namespace v8::internal::maglev { class ValueNode; }
namespace i = v8::internal;
using Value = i::maglev::ValueNode*;
using Table = i::compiler::turboshaft::SnapshotTable<Value>;
int main() {
  i::AccountingAllocator allocator;
  size_t checks = 0;
  // Opaque identities are never dereferenced; the real table stores pointers.
  alignas(void*) unsigned char identities[3][sizeof(void*)]{};
  Value a = reinterpret_cast<Value>(identities[0]);
  Value b = reinterpret_cast<Value>(identities[1]);
  Value c = reinterpret_cast<Value>(identities[2]);
  for (unsigned repeat = 0; repeat < 20; ++repeat) {
    for (size_t count : {0, 1, 2, 16, 64, 1024, 4096}) {
      {
        i::Zone zone(&allocator, "SnapshotTable log transfer regression");
        Table table(&zone);
        std::vector<Table::Key> keys;
        for (size_t n = 0; n < count; ++n) { keys.push_back(table.NewKey()); }
        table.StartNewSnapshot();
        for (auto key : keys) {
          CHECK_EQ(table.Get(key), nullptr);
          CHECK(table.Set(key, a));
          CHECK(!table.Set(key, a));
          checks += 3;
        }
        auto base = table.Seal();
        table.StartNewSnapshot(base);
        for (size_t n = 0; n < count; ++n) {
          CHECK(table.Set(keys[n], n % 2 ? b : c));
          ++checks;
        }
        auto left = table.Seal();
        table.StartNewSnapshot(base);
        for (size_t n = 0; n < count; ++n) {
          CHECK_EQ(table.Get(keys[n]), a);
          CHECK_EQ(table.Set(keys[n], n % 2 ? a : c), n % 2 == 0);
          checks += 2;
        }
        auto right = table.Seal();
        table.StartNewSnapshot({left, right}, [](Table::Key, v8::base::Vector<const Value> values) {
          CHECK_EQ(values.size(), 2);
          return values[0] == values[1] ? values[0] : nullptr;
        });
        for (size_t n = 0; n < count; ++n) {
          CHECK_EQ(table.Get(keys[n]), n % 2 ? nullptr : c);
          CHECK_EQ(table.GetPredecessorValue(keys[n], 0), n % 2 ? b : c);
          CHECK_EQ(table.GetPredecessorValue(keys[n], 1), n % 2 ? a : c);
          checks += 3;
        }
        table.Seal();
        table.StartNewSnapshot(left);
        for (size_t n = 0; n < count; ++n) {
          CHECK_EQ(table.Get(keys[n]), n % 2 ? b : c);
          ++checks;
        }
        CHECK(table.Seal() == left);
        table.StartNewSnapshot();
        for (auto key : keys) { CHECK_EQ(table.Get(key), nullptr); ++checks; }
        table.Seal();
        ++checks;
      }
      CHECK_EQ(allocator.GetCurrentMemoryUsage(), 0);
      ++checks;
    }
  }
  std::printf("PASS: %zu real SnapshotTable log growth, branch, merge and rollback checks\n", checks);
}
