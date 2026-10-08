// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <llvm/Support/Threading.h>
#include <array>
#include <atomic>
#include <cstdio>
#include <exception>
#include <thread>
static_assert(__cplusplus >= 202002L);
static_assert(LLVM_THREADING_USE_STD_CALL_ONCE == 1);
int main() {
    try {
        llvm::once_flag once;
        std::atomic<unsigned> calls{0}, checks{0}, failures{0};
        unsigned payload = 0;
        std::array<std::jthread, 8> threads;
        for (auto& thread : threads) {
            thread = std::jthread([&] {
                if (!llvm::get_threadid()) { ++failures; }
                ++checks;
                for (unsigned i = 0; i < 1000; ++i) {
                    llvm::call_once(once, [&] { payload = 0x6157; ++calls; });
                    if (payload != 0x6157) { ++failures; }
                    ++checks;
                }
            });
        }
        for (auto& thread : threads) { thread.join(); }
        ++checks;
        if (calls != 1 || failures || checks != 8009) { return 1; }
        std::printf("PASS: %u LLVM threading checks\n", checks.load());
    } catch (const std::exception& error) {
        std::fprintf(stderr, "FAIL: %s\n", error.what());
        return 1;
    }
    return 0;
}
