// Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.
#include <grpc/support/port_platform.h>
#include "src/core/lib/iomgr/wakeup_fd_posix.h"
#include <cstdio>
#include <cerrno>
#include <fcntl.h>
static bool inject_failure = true;
static int attempts = 0;
static grpc_error_handle fail_wakeup_init(grpc_wakeup_fd* fd) {
    ++attempts;
    if (inject_failure) {
        fd->read_fd = fd->write_fd = -1;
        return absl::ResourceExhaustedError("injected wakeup initialization failure");
    }
    return grpc_wakeup_fd_init(fd);
}
#define grpc_wakeup_fd_init fail_wakeup_init
#include "src/core/lib/iomgr/ev_poll_posix.cc"
#undef grpc_wakeup_fd_init
#undef NDEBUG
#include <cassert>

int main() {
    constexpr int iterations = 25;
    grpc_wakeup_fd_global_init();
    int failures = 0;
    for (bool fork_tracking : {false, true}) {
        track_fds_for_fork = fork_tracking;
        gpr_mu_init(&fork_fd_list_mu);
        for (bool with_handle : {false, true}) {
            for (int index = 0; index < iterations; ++index) {
                grpc_pollset set{};
                gpr_mu* mu;
                pollset_init(&set, &mu);
                grpc_pollset_worker* handle = nullptr;
                gpr_mu_lock(mu);
                auto error = pollset_work(&set, with_handle ? &handle : nullptr,
                    grpc_core::Timestamp::InfPast());
                gpr_mu_unlock(mu);
                assert(error.code() == absl::StatusCode::kResourceExhausted);
                if (handle != nullptr || set.local_wakeup_cache != nullptr
                        || fork_fd_list_head != nullptr) {
                    ++failures;
                }
                // A successful later call must still allocate and cache a valid
                // wakeup descriptor; cached calls must not retry initialization.
                inject_failure = false;
                set.shutting_down = set.called_shutdown = 1;
                gpr_mu_lock(mu);
                auto recovered = pollset_work(&set, with_handle ? &handle : nullptr,
                    grpc_core::Timestamp::InfPast());
                gpr_mu_unlock(mu);
                assert(recovered.ok() && handle == nullptr);
                assert(set.local_wakeup_cache != nullptr);
                const int fd = set.local_wakeup_cache->fd.read_fd;
                assert(fd >= 0 && fcntl(fd, F_GETFD) != -1);
                inject_failure = true;
                const int before = attempts;
                gpr_mu_lock(mu);
                auto cached = pollset_work(&set, with_handle ? &handle : nullptr,
                    grpc_core::Timestamp::InfPast());
                gpr_mu_unlock(mu);
                assert(cached.ok() && handle == nullptr && attempts == before);
                pollset_destroy(&set);
                assert(fcntl(fd, F_GETFD) == -1 && errno == EBADF);
                if (fork_fd_list_head != nullptr) {
                    ++failures;
                }
            }
        }
        gpr_mu_destroy(&fork_fd_list_mu);
    }
    std::printf("%d initializations (failure/recovery pairs); %d invalid cleanup states\n", attempts, failures);
    return failures ? 1 : 0;
}
