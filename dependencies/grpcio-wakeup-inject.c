/* Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0. */
#define _GNU_SOURCE
#include <stdatomic.h>
#include <errno.h>
#include <stddef.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <unistd.h>

static _Atomic int injection_mode;
static _Atomic unsigned matched_calls;
static _Atomic unsigned failures;

void grpcio_wakeup_arm(int mode) {
    atomic_store(&matched_calls, 0);
    atomic_store(&failures, 0);
    atomic_store(&injection_mode, mode);
}
unsigned grpcio_wakeup_calls(void) { return atomic_load(&matched_calls); }
unsigned grpcio_wakeup_failures(void) { return atomic_load(&failures); }

ssize_t write(int fd, const void *data, size_t size) {
    int mode = atomic_load(&injection_mode);
    if (mode && size == 1 && *(const char *)data == '1') {
        struct sockaddr_storage address;
        socklen_t length = sizeof(address);
        if (getsockname(fd, (struct sockaddr *)&address, &length) == 0 && address.ss_family == AF_UNIX) {
            unsigned call = atomic_fetch_add(&matched_calls, 1);
            if ((mode == 1 && call < 2) || mode == 2 || mode == 3) {
                atomic_fetch_add(&failures, 1);
                errno = mode == 1 ? EINTR : EBADF;
                return mode == 3 ? 0 : -1;
            }
        }
    }
    return syscall(SYS_write, fd, data, size);
}
