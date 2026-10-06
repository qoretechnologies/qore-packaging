// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <array>
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <type_traits>
#include "src/objects/tagged-field.h"

using Digit = v8::internal::UnalignedValueMember<uint64_t>;
static_assert(std::is_trivially_copyable_v<Digit>);
static_assert(sizeof(Digit) == sizeof(uint64_t));
static_assert(std::is_trivially_copyable_v<std::atomic<uint32_t>>);
static_assert(sizeof(std::atomic<uint32_t>) == sizeof(uint32_t));
static size_t checks = 0;
static void Check(bool condition) {
    ++checks;
    if (!condition) {
        std::fprintf(stderr, "failed check %zu\n", checks);
        std::abort();
    }
}

// Identical byte operations to MutableBigInt::InitializeDigits and
// NativeModuleDeserializer::ReadTieringBudget, on their real target types.
static void InitializeDigits(Digit* digits, uint32_t length, uint8_t value) {
    memset(digits, value, length * sizeof(uint64_t));
}
static void ReadTieringBudget(std::atomic<uint32_t>* destination, const uint8_t* source,
        size_t available, size_t count) {
    size_t size = count * sizeof(uint32_t);
    if (size > available) {
        return;
    }
    memcpy(destination, source, size);
}

int main() {
    constexpr uint64_t sentinel = UINT64_C(0x123456789abcdef0);
    struct Digits {
        uint64_t before;
        Digit digits[65];
        uint64_t after;
    } block;
    for (unsigned value = 0; value < 256; ++value) {
        uint64_t expected = 0;
        std::memset(&expected, value, sizeof(expected));
        for (uint32_t count = 0; count <= 65; ++count) {
            block.before = block.after = sentinel;
            for (auto& digit : block.digits) { digit.set_value(sentinel); }
            InitializeDigits(block.digits, count, static_cast<uint8_t>(value));
            Check(block.before == sentinel && block.after == sentinel);
            for (uint32_t i = 0; i < 65; ++i) {
                Check(block.digits[i].value() == (i < count ? expected : sentinel));
            }
        }
    }
    constexpr uint32_t atomic_sentinel = 0xfedcba98;
    struct Budgets {
        uint64_t before;
        std::atomic<uint32_t> values[65];
        uint64_t after;
    } budgets;
    for (unsigned shift = 0; shift < 32; ++shift) {
        std::array<uint32_t, 65> expected;
        for (size_t i = 0; i < expected.size(); ++i) {
            expected[i] = (i & 1) ? ~(uint32_t{1} << shift) : uint32_t{1} << shift;
        }
        // Copy from each byte alignment; serialized input need not be aligned.
        for (size_t alignment = 0; alignment < 8; ++alignment) {
            std::array<uint8_t, sizeof(expected) + 8> serialized{};
            std::memcpy(serialized.data() + alignment, expected.data(), sizeof(expected));
            for (size_t count = 0; count <= expected.size(); ++count) {
                for (bool truncated : {false, true}) {
                    budgets.before = budgets.after = sentinel;
                    for (auto& value : budgets.values) { value.store(atomic_sentinel); }
                    size_t bytes = count * sizeof(uint32_t);
                    size_t available = truncated && bytes ? bytes - 1 : bytes;
                    ReadTieringBudget(budgets.values, serialized.data() + alignment, available, count);
                    Check(budgets.before == sentinel && budgets.after == sentinel);
                    for (size_t i = 0; i < expected.size(); ++i) {
                        Check(budgets.values[i].load() == ((!truncated && i < count)
                            ? expected[i] : atomic_sentinel));
                    }
                }
            }
        }
    }
    std::printf("%zu BigInt and atomic representation checks passed\n", checks);
}
