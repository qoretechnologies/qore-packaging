// Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.
#include <cerrno>
#include <cassert>
#include <cstdio>
#include <fcntl.h>
#include <unistd.h>

static int mode;
static unsigned calls;
static ssize_t intercepted_write(int fd, const void* data, size_t size) {
    ++calls;
    if (mode == 1 && calls <= 2) {
        errno = EINTR;
        return -1;
    }
    if (mode == 2 || mode == 4) {
        errno = mode == 2 ? EBADF : EAGAIN;
        return -1;
    }
    if (mode == 3) {
        return 0;
    }
    return ::write(fd, data, size);
}
#define write intercepted_write
#include "grpcio-wakeup-impl.h"
#undef write

int main() {
    int fds[2];
    assert(pipe2(fds, O_NONBLOCK | O_CLOEXEC) == 0);
    for (mode = 0; mode < 5; ++mode) {
        calls = 0;
#ifdef BASELINE
        _unified_socket_write_impl(fds[1]);
#else
        const bool result = _unified_socket_write_impl(fds[1]);
        assert(result == (mode < 2));
#endif
        if (mode < 2) {
            char byte = 0;
            assert(read(fds[0], &byte, 1) == 1 && byte == '1');
            assert(calls == (mode == 0 ? 1u : 3u));
        } else {
            char byte;
            assert(read(fds[0], &byte, 1) == -1 && errno == EAGAIN);
            assert(calls == 1);
        }
    }
    assert(close(fds[0]) == 0);
    assert(close(fds[1]) == 0);
    std::puts("PASS: successful wakeup, repeated EINTR, EBADF, zero-length result and EAGAIN");
}
