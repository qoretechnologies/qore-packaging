// PhaseScope excerpt: Copyright 2014 the V8 project authors. BSD-3-Clause; see LICENSE.
// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include "src/tracing/trace-event.h"

namespace {
uint64_t checks = 0;

void require(bool condition) {
    ++checks;
    if (!condition) {
        std::abort();
    }
}

class Controller final : public v8::TracingController {
public:
    void UpdateTraceEventDuration(const uint8_t* flag, const char* name, uint64_t handle) override {
        require(flag == expected_flag);
        require(name == expected_name);
        require(handle == expected_handle);
        ++calls;
    }
    const uint8_t* expected_flag = nullptr;
    const char* expected_name = nullptr;
    uint64_t expected_handle = 0;
    uint64_t calls = 0;
};
Controller controller;

// The production table's allocator methods are hidden in libnode. Embed the
// exact PhaseScope definition in a minimal table exposing its one accessed field.
// No constructor/destructor statement in the tested scope is changed.
struct NodeOriginTable {
    const char* current_phase_name_ = "unknown";
  class V8_NODISCARD PhaseScope final {
   public:
    PhaseScope(NodeOriginTable* origins, const char* phase_name)
        : origins_(origins) {
      if (origins != nullptr) {
        prev_phase_name_ = origins->current_phase_name_;
        origins->current_phase_name_ =
            phase_name == nullptr ? "unnamed" : phase_name;
      }
    }

    ~PhaseScope() {
      if (origins_) origins_->current_phase_name_ = prev_phase_name_;
    }

    PhaseScope(const PhaseScope&) = delete;
    PhaseScope& operator=(const PhaseScope&) = delete;

   private:
    NodeOriginTable* const origins_;
    const char* prev_phase_name_;
  };
};

void check_phase(NodeOriginTable& table, const char* expected) {
    require(std::strcmp(table.current_phase_name_, expected) == 0);
}

__attribute__((noinline)) void phase_case(NodeOriginTable& table, bool outer, bool inner,
                                        const char* outer_name, const char* inner_name) {
    check_phase(table, "unknown");
    const char* first = outer ? (outer_name ? outer_name : "unnamed") : "unknown";
    {
        NodeOriginTable::PhaseScope scope(outer ? &table : nullptr, outer_name);
        check_phase(table, first);
        {
            NodeOriginTable::PhaseScope nested(inner ? &table : nullptr, inner_name);
            check_phase(table, inner ? (inner_name ? inner_name : "unnamed") : first);
        }
        check_phase(table, first);
    }
    check_phase(table, "unknown");
}

__attribute__((noinline)) void trace_case(bool initialize, bool active, bool clear, uint64_t handle) {
    uint8_t flag = active ? 1 : 0;
    static const char name[] = "guarded-state";
    const uint64_t before = controller.calls;
    controller.expected_flag = &flag;
    controller.expected_name = name;
    controller.expected_handle = handle;
    {
        v8::internal::tracing::ScopedTracer tracer;
        if (initialize) {
            tracer.Initialize(&flag, name, handle);
        }
        if (clear) {
            flag = 0;
        }
    }
    require(controller.calls == before + (initialize && active && !clear ? 1 : 0));
}
}

// Use the real inline ScopedTracer implementation with an observable callback.
v8::TracingController* v8::internal::tracing::TraceEventHelper::GetTracingController() {
    return &controller;
}

int main() {
    NodeOriginTable table;
    const char* names[] = {nullptr, "", "outer", "inner"};
    for (unsigned iteration = 0; iteration < 1000; ++iteration) {
        for (unsigned mask = 0; mask < 4; ++mask) {
            for (const char* outer : names) {
                for (const char* inner : names) {
                    phase_case(table, mask & 1, mask & 2, outer, inner);
                }
            }
        }
        for (unsigned mask = 0; mask < 8; ++mask) {
            for (unsigned bit = 0; bit < 64; ++bit) {
                trace_case(mask & 1, mask & 2, mask & 4, uint64_t{1} << bit);
                trace_case(mask & 1, mask & 2, mask & 4, ~(uint64_t{1} << bit));
            }
        }
    }
    std::printf("%llu guarded-state checks passed\n",
                static_cast<unsigned long long>(checks));
}
