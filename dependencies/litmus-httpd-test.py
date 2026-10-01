#!/usr/bin/python3
# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Run all default WebDAV tests against a private, unprivileged Apache server."""
import argparse
from contextlib import contextmanager
import grp
import os
from pathlib import Path
import pwd
import re
import select
import shutil
import signal
import subprocess
import tempfile
import time

# Explicitly approved 2026-10-01; see litmus.rst for the Apache source analysis.
EXPECTED_WARNINGS = frozenset({
    'COPY Destination header should allow absolute path (RFC4918:S10.3): got 400 Bad Request',
    'PUT failed with 400 not 423',
    'LOCK on unmapped url returned 200 not 201 (RFC4918:S7.3)',
})


def validate_output(output):
    warnings = re.findall(r'WARNING: ([^\r\n]+)', output)
    unexpected = set(warnings) - EXPECTED_WARNINGS
    if unexpected:
        raise RuntimeError('Unexpected Litmus diagnostics: ' + repr(sorted(unexpected)))
    summaries = re.findall(r"summary for `([^']+)': of (\d+) tests run: (\d+) passed, (\d+) failed", output)
    expected = {'basic': 16, 'copymove': 13, 'props': 33, 'locks': 40, 'http': 4}
    if len(summaries) != len(expected) or {
            name: int(total) for name, total, passed, failed in summaries} != expected:
        raise RuntimeError('Missing or incomplete default Litmus suites: ' + repr(summaries))
    if any(total != passed or int(failed) for _, total, passed, failed in summaries):
        raise RuntimeError('Litmus reports failing tests')
    return warnings


def await_startup(stream, timeout=20):
    """Subscribe to Apache's startup event; EOF and a deadline are fatal."""
    deadline = time.monotonic() + timeout
    output = bytearray()
    while b'resuming normal operations' not in output:
        ready, _, _ = select.select([stream], [], [], max(0, deadline - time.monotonic()))
        if not ready:
            raise RuntimeError('Apache startup deadline exceeded: ' + output.decode(errors='replace'))
        data = os.read(stream.fileno(), 4096)
        if not data:
            raise RuntimeError('Apache exited before startup: ' + output.decode(errors='replace'))
        output.extend(data)
    return output.decode(errors='replace')


def module_directives(modules, compiled):
    """Honor Apache's compiled-in modules, including SUSE's static MPM."""
    directives = []
    for name in ('mpm_event', 'unixd', 'authz_core', 'dav', 'dav_fs'):
        if name + '.c' in compiled or (name == 'mpm_event' and
                re.search(r'\b(?:mpm_)?(?:event|prefork|worker)\.c', compiled)):
            continue
        library = modules / ('mod_' + name + '.so')
        if not library.is_file():
            raise RuntimeError('Required Apache module is missing: ' + str(library))
        directives.append(f'LoadModule {name}_module "{library}"')
    return directives


@contextmanager
def running_server(command):
    server = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              start_new_session=True)
    try:
        print(await_startup(server.stdout), end='', flush=True)
        yield
    finally:
        try:
            os.killpg(server.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            output, _ = server.communicate(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(server.pid, signal.SIGKILL)
            server.communicate()
            raise
        print(output.decode(errors='replace'), end='', flush=True)


def run(litmus, installed=False):
    litmus = litmus.resolve(strict=True)
    if os.getuid() == 0:
        raise RuntimeError('The private Apache fixture must run unprivileged')
    httpd = shutil.which('httpd') or shutil.which('apache2')
    if not httpd:
        raise RuntimeError('Apache server executable is missing')
    modules = next((p for p in (Path('/usr/lib64/httpd/modules'), Path('/usr/lib64/apache2'))
                    if (p / 'mod_dav.so').is_file()), None)
    if modules is None:
        raise RuntimeError('Apache WebDAV modules are missing')
    compiled = subprocess.check_output([httpd, '-l'], text=True)
    with tempfile.TemporaryDirectory(prefix='litmus-httpd-') as directory:
        root = Path(directory)
        (root / 'dav').mkdir()
        config = root / 'httpd.conf'
        config.write_text('\n'.join([
            f'ServerRoot "{root}"', 'ServerName localhost', 'Listen 127.0.0.1:18080',
            *module_directives(modules, compiled),
            f'User {pwd.getpwuid(os.getuid()).pw_name}', f'Group {grp.getgrgid(os.getgid()).gr_name}',
            f'PidFile "{root}/httpd.pid"', 'ErrorLog /dev/stderr', 'LogLevel notice',
            f'DocumentRoot "{root}/dav"', f'DavLockDB "{root}/locks"',
            f'<Directory "{root}/dav">', 'Require all granted', 'DAV On', '</Directory>', '']))
        subprocess.run([httpd, '-t', '-f', str(config)], check=True)
        with running_server([httpd, '-DFOREGROUND', '-f', str(config)]):
            env = os.environ.copy()
            for key in ('TESTS', 'TESTROOT', 'http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY'):
                env.pop(key, None)
            env['LC_ALL'] = 'C.UTF-8'
            if not installed:
                env['TESTROOT'] = str(litmus.parent)
            result = subprocess.run([str(litmus), '--no-colour', 'http://127.0.0.1:18080/'],
                                    env=env, cwd=root, capture_output=True, text=True, timeout=180)
            output = result.stdout + result.stderr
            print(output, end='', flush=True)
            result.check_returncode()
            warnings = validate_output(output)
            print(f'All 106 tests passed; {len(warnings)} approved Apache diagnostics retained.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('litmus', type=Path)
    parser.add_argument('--installed', action='store_true')
    args = parser.parse_args()
    run(args.litmus, args.installed)
