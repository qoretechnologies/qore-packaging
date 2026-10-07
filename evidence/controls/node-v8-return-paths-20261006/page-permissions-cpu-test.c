/* Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT */
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include "cpu_features.h"
static void* check(void* arg) {
    (void)arg;
    for (unsigned i = 0; i < 10000; ++i) {
        cpu_check_features();
        if (!!x86_cpu_enable_sse2 != !!__builtin_cpu_supports("sse2")
            || !!x86_cpu_enable_ssse3 != !!__builtin_cpu_supports("ssse3")
            || !!x86_cpu_enable_simd != !!(__builtin_cpu_supports("sse2")
                && __builtin_cpu_supports("sse4.2") && __builtin_cpu_supports("pclmul"))) {
            abort();
        }
    }
    return NULL;
}
int main(void) {
    pthread_t threads[4];
    for (unsigned i = 0; i < 4; ++i) {
        if (pthread_create(&threads[i], NULL, check, NULL)) { return 1; }
    }
    for (unsigned i = 0; i < 4; ++i) {
        if (pthread_join(threads[i], NULL)) { return 1; }
    }
    puts("40000 concurrent CPU detection checks passed");
    return 0;
}
