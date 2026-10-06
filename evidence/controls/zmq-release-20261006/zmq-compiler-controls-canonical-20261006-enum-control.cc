// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <cstdio>
enum qzmq_option_type {
    QZOT_INT = 0,
    QZOT_BIN = 1,
    QZOT_INT64 = 2,
    QZOT_STR = 3,
    QZOT_BOOL = 4,
    QZOT_CURVEKEY = 5,
};


__attribute__((noinline)) int query(qzmq_option_type type, int input) {
    int rc;
    switch (type) {
        case QZOT_INT: { rc = input + 0; break; }
        case QZOT_BIN: { rc = input + 1; break; }
        case QZOT_INT64: { rc = input + 2; break; }
        case QZOT_STR: { rc = input + 3; break; }
        case QZOT_BOOL: { rc = input + 4; break; }
        case QZOT_CURVEKEY: { rc = input + 5; break; }

    }
    return rc;
}
int main() {
    unsigned checks = 0;
    for (int n = 0; n < 10000; ++n) {
        for (int value = 0; value < 6; ++value) {
            if (query(static_cast<qzmq_option_type>(value), n) != n + value) { return 1; }
            ++checks;
        }
    }
    std::printf("%u exhaustive option-type checks passed\n", checks);
}
