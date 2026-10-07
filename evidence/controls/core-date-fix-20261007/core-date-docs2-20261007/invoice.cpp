// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <qore/Qore.h>
#include <memory>
#include <stdexcept>
struct Runtime {
    Runtime() { qore_init(QL_MIT, "UTF-8", false, QLO_DISABLE_SIGNAL_HANDLING); }
    ~Runtime() { qore_cleanup(); }
};
int main() {
    Runtime runtime;
       DateTime invoice_time(nullptr, "2026-10-07T09:00:00Z");
       std::unique_ptr<DateTime> payment_period(DateTime::makeRelative(0, 1, 0));
       std::unique_ptr<DateTime> due_date(invoice_time.add(*payment_period));
       
    if (!due_date->isEqual(DateTime(nullptr, "2026-11-07T09:00:00Z"))) {
        throw std::runtime_error("invoice due date differs from documented calendar sum");
    }
}
