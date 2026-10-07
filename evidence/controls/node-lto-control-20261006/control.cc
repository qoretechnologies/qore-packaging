// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <cstdint>
#include <cstdio>
#include <cstdlib>
extern "C" void PushAllRegistersAndIterateStack(void*, void*, void (*)(void*, void*, const void*));
struct State { unsigned remaining; unsigned calls; std::uintptr_t canary; };
static void Check(void* expected, void* opaque, const void* bottom) {
    State* state = static_cast<State*>(opaque);
    if (expected != &state->canary || state->canary != 0x12345678U ||
        reinterpret_cast<std::uintptr_t>(bottom) % 16 != 0) { std::abort(); }
    const auto* words = static_cast<const std::uintptr_t*>(bottom);
    if (words[5] != 0xCDCDCDU) { std::abort(); }
    ++state->calls;
    if (state->remaining > 0) {
        --state->remaining;
        PushAllRegistersAndIterateStack(expected, opaque, Check);
    }
}
int main() {
    unsigned checks = 0;
    for (unsigned count = 0; count < 10000; ++count) {
        for (unsigned depth = 0; depth < 16; ++depth) {
            State state{depth, 0, 0x12345678U};
            PushAllRegistersAndIterateStack(&state.canary, &state, Check);
            if (state.calls != depth + 1 || state.remaining != 0 || state.canary != 0x12345678U) { std::abort(); }
            checks += state.calls;
        }
    }
    std::printf("%u stack callback checks passed\n", checks);
}
