// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <qore/Qore.h>
#include <qore/intern/qore_date_private.h>
#include <cstdio>
#include <cstdlib>
#include <limits>

struct QoreRuntimeScope {
    QoreRuntimeScope() {
        qore_init(QL_MIT, "UTF-8", false, QLO_DISABLE_SIGNAL_HANDLING);
    }
    ~QoreRuntimeScope() {
        qore_cleanup();
    }
};

int main() {
    QoreRuntimeScope runtime;
    unsigned checks = 0;
    for (int hours : {-24, -1, 0, 1, 24, std::numeric_limits<int>::min(), std::numeric_limits<int>::max()}) {
        for (int minutes : {-59, -1, 0, 1, 59}) {
            for (int seconds : {-59, -1, 0, 1, 59}) {
                for (int us : {-999999, -1, 0, 1, 999999}) {
                    // Restrict extrema to normalization that cannot exceed the hour field.
                    if ((hours == std::numeric_limits<int>::min() && (minutes < 0 || seconds < 0 || us < 0))
                            || (hours == std::numeric_limits<int>::max() && (minutes > 0 || seconds > 0 || us > 0))) {
                        continue;
                    }
                    const int64 total = static_cast<int64>(hours) * MICROSECS_PER_HOUR
                        + static_cast<int64>(minutes) * MICROSECS_PER_MINUTE
                        + static_cast<int64>(seconds) * MICROSECS_PER_SEC + us;
                    qore_relative_time value;
                    value.set(0, 0, 0, hours, minutes, seconds, us);
                    qore_relative_time expected;
                    int64 remainder = total;
                    const int expected_hours = static_cast<int>(remainder / MICROSECS_PER_HOUR);
                    remainder %= MICROSECS_PER_HOUR;
                    const int expected_minutes = static_cast<int>(remainder / MICROSECS_PER_MINUTE);
                    remainder %= MICROSECS_PER_MINUTE;
                    expected.set(0, 0, 0, expected_hours, expected_minutes,
                        static_cast<int>(remainder / MICROSECS_PER_SEC),
                        static_cast<int>(remainder % MICROSECS_PER_SEC));
                    if (value.getRelativeMicroseconds() != total || value.compare(expected)
                            || expected.compare(value)) {
                        std::fprintf(stderr, "FAIL: %d %d %d %d total=%lld\n", hours, minutes, seconds, us,
                            static_cast<long long>(total));
                        return 1;
                    }
                    ++checks;
                }
            }
        }
    }
    std::printf("PASS: %u signed-duration boundary cases\n", checks);
}
