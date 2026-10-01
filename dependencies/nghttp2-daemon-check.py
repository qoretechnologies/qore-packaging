#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Exercise nghttpx's systemd daemon startup with real and failing chdir."""
import errno
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import tempfile


def main(binary, memory_check=False):
    binary = str(Path(binary).resolve())
    with tempfile.TemporaryDirectory(prefix="nghttp2-daemon-") as temporary:
        root = Path(temporary)
        source = root / "systemd.c"
        shim = root / "systemd.so"
        source.write_text('''#define _GNU_SOURCE
#include <errno.h>
#include <stdlib.h>
#include <sys/syscall.h>
#include <unistd.h>
int sd_booted(void) { return 1; }
int chdir(const char *path) {
    const char *error = getenv("NGHTTP2_TEST_CHDIR_ERRNO");
    if (error && *error) {
        errno = atoi(error);
        return -1;
    }
    return syscall(SYS_chdir, path);
}
''')
        subprocess.run(["cc", "-shared", "-fPIC", "-Wall", "-Wextra", "-Werror",
                        str(source), "-o", str(shim)], check=True)
        command = [binary, "--daemon", "--conf=/dev/null",
                   "--frontend=unix:" + str(root / "frontend") + ";no-tls"]
        if memory_check:
            command = ["valgrind", "--error-exitcode=99", "--leak-check=full",
                       "--errors-for-leak-kinds=definite,indirect", *command]
        env = {**os.environ, "LC_ALL": "C", "LD_PRELOAD": str(shim),
               "NOTIFY_SOCKET": str(root / "notify")}
        for error in (errno.EACCES, errno.ENOENT):
            result = subprocess.run(command, env={**env, "NGHTTP2_TEST_CHDIR_ERRNO": str(error)},
                                    capture_output=True, text=True, timeout=60)
            sys.stdout.write(result.stderr)
            if result.returncode != 255 or "Failed to daemonize: " + os.strerror(error) not in result.stderr:
                raise AssertionError((error, result.returncode, result.stdout, result.stderr))
        # The real chdir must reach systemd readiness. Block on its notification,
        # then request graceful shutdown: no startup sleeps or readiness polling.
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notification:
            notification.bind(env["NOTIFY_SOCKET"])
            notification.settimeout(60)
            with tempfile.TemporaryFile(mode="w+") as log:
                process = subprocess.Popen(command, env={**env, "NGHTTP2_TEST_CHDIR_ERRNO": ""},
                                           stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    ready = notification.recv(4096)
                    if ready.startswith(b"MAINPID="):
                        if ready.strip() != ("MAINPID=" + str(process.pid)).encode():
                            raise AssertionError(ready)
                        ready = notification.recv(4096)
                    if b"READY=1" not in ready:
                        raise AssertionError(ready)
                    process.send_signal(signal.SIGQUIT)
                    status = process.wait(timeout=60)
                    if status != 0:
                        raise AssertionError("Daemon shutdown status: " + str(status))
                finally:
                    if process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    log.seek(0)
                    sys.stdout.write(log.read())
    print("nghttpx daemon: permission error, missing directory and successful startup passed")


if __name__ == "__main__":
    main(sys.argv[1], "--valgrind" in sys.argv[2:])
