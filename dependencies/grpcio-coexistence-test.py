#!/usr/bin/env python3
# Copyright 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Keep Python's embedded gRPC registry independent of the system libgrpc."""
import subprocess
import sys
import os

import pytest


@pytest.mark.parametrize("system_first", [False, True])
def test_shared_grpc_coexistence(system_first):
    imports = ["import grpc", "system_grpc = ctypes.CDLL('libgrpc.so.37')"]
    if system_first:
        imports.reverse()
    script = "import ctypes\n" + "\n".join(imports) + "\n" + '''
from concurrent.futures import ThreadPoolExecutor

def echo(value, context):
    if not value:
        context.abort(grpc.StatusCode.INVALID_ARGUMENT, "empty request")
    return value

with ThreadPoolExecutor(max_workers=2) as executor:
    server = grpc.server(executor)
    server.add_generic_rpc_handlers((grpc.method_handlers_generic_handler(
        "coexistence.Echo", {"Echo": grpc.unary_unary_rpc_method_handler(echo)}),))
    port = server.add_insecure_port("127.0.0.1:0")
    assert port > 0
    server.start()
    try:
        with grpc.insecure_channel(f"127.0.0.1:{port}") as channel:
            call = channel.unary_unary("/coexistence.Echo/Echo")
            payload = "Qore → gRPC".encode()
            assert call(payload, timeout=10) == payload
            try:
                call(b"", timeout=10)
            except grpc.RpcError as error:
                assert error.code() == grpc.StatusCode.INVALID_ARGUMENT
                assert error.details() == "empty request"
            else:
                raise AssertionError("invalid request succeeded")
    finally:
        assert server.stop(0).wait(10)
print("shared and embedded gRPC coexist; normal and negative RPCs passed")
'''
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", script],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not result.stderr, result.stderr
    assert "normal and negative RPCs passed" in result.stdout


@pytest.mark.parametrize("bind_port", [False, True])
@pytest.mark.parametrize("stop_first", [False, True])
def test_unstarted_server_teardown(bind_port, stop_first):
    script = '''
import gc
import socket
import grpc
server = grpc.server(None, options=(("grpc.so_reuseport", 0),))
'''
    if bind_port:
        script += 'port = server.add_insecure_port("127.0.0.1:0")\nassert port > 0\n'
    if stop_first:
        script += 'assert server.stop(0).wait(10)\n'
    script += 'del server\ngc.collect()\n'
    if bind_port:
        script += '''with socket.socket() as listener:
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", port))
'''
    script += 'print("unstarted server released its resources")\n'
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", script],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not result.stderr, result.stderr
    assert "released its resources" in result.stdout


@pytest.mark.parametrize("invalid_channel", [False, True])
def test_tls_credential_lifetimes(invalid_channel):
    script = '''
import gc
import os
from pathlib import Path
import grpc
root = Path(os.environ["GRPC_TEST_ROOT"]) / "credentials"
key = (root / "server1.key").read_bytes()
certificate = (root / "server1.pem").read_bytes()
for repeat in range(20):
    credentials = grpc.ssl_server_credentials(((key, certificate),))
    server = grpc.server(None)
    assert server.add_secure_port("127.0.0.1:0", credentials) > 0
    del server, credentials
    gc.collect()
try:
    grpc.ssl_server_credentials(())
except ValueError:
    pass
else:
    raise AssertionError("empty credentials accepted")
'''
    if invalid_channel:
        script += '''
class InvalidPointer:
    def __int__(self):
        raise RuntimeError("pointer conversion failed")
for repeat in range(5):
    for invalid in ({"foo": "bar"}, (("key",),), "str", (("ptr", InvalidPointer()),)):
        try:
            grpc.insecure_channel("localhost:8080", options=invalid)
        except (ValueError, RuntimeError):
            pass
        else:
            raise AssertionError("invalid arguments accepted")
gc.collect()
'''
    script += 'print("TLS credential and server lifetimes passed")\n'
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", script],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not result.stderr, result.stderr
    assert "TLS credential and server lifetimes passed" in result.stdout


def test_async_completion_queue_global_lifetime():
    script = '''
import asyncio
import gc
import grpc

async def lifetime():
    server = grpc.aio.server()
    assert server.add_insecure_port("127.0.0.1:0") > 0
    await server.start()
    try:
        async with grpc.aio.insecure_channel("127.0.0.1:1"):
            pass
    finally:
        await server.stop(0)

for repeat in range(20):
    asyncio.run(lifetime())
    gc.collect()
    queues = [obj for obj in gc.get_objects()
              if type(obj).__module__ == "grpc._cython.cygrpc"
              and type(obj).__name__ == "PollerCompletionQueue"]
    assert not queues, "completion queue retained after its final user"
print("completion queue released after every async lifetime")
'''
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", script],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not result.stderr, result.stderr
    assert "released after every async lifetime" in result.stdout


def test_async_completion_queue():
    script = '''
import asyncio
import grpc
from grpc._cython import cygrpc

async def main():
    entered = asyncio.Event()
    cancelled = asyncio.Event()
    release = asyncio.Event()

    async def echo(value, context):
        if not value:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "empty request")
        return value

    async def block(value, context):
        entered.set()
        try:
            await release.wait()
        except asyncio.CancelledError:
            cancelled.set()
            raise
        return value

    async def stream(value, context):
        for index in range(5):
            yield value + bytes((index,))

    server = grpc.aio.server()
    server.add_generic_rpc_handlers((grpc.method_handlers_generic_handler(
        "completion.Echo", {
            "Echo": grpc.unary_unary_rpc_method_handler(echo),
            "Block": grpc.unary_unary_rpc_method_handler(block),
            "Stream": grpc.unary_stream_rpc_method_handler(stream),
        }),))
    port = server.add_insecure_port("127.0.0.1:0")
    assert port > 0
    await server.start()
    try:
        async with grpc.aio.insecure_channel(f"127.0.0.1:{port}") as channel:
            echo_call = channel.unary_unary("/completion.Echo/Echo")
            payloads = [f"Qore → async {index}".encode() for index in range(32)]
            assert await asyncio.gather(*(
                echo_call(value, timeout=10) for value in payloads)) == payloads
            try:
                await echo_call(b"", timeout=10)
            except grpc.aio.AioRpcError as error:
                assert error.code() == grpc.StatusCode.INVALID_ARGUMENT
                assert error.details() == "empty request"
            else:
                raise AssertionError("empty async request succeeded")
            stream_call = channel.unary_stream("/completion.Echo/Stream")
            values = [value async for value in stream_call(b"stream", timeout=10)]
            assert values == [b"stream" + bytes((index,)) for index in range(5)]
            for repeat in range(10):
                entered.clear()
                cancelled.clear()
                blocked = channel.unary_unary("/completion.Echo/Block")(b"cancel", timeout=10)
                await asyncio.wait_for(entered.wait(), 10)
                assert blocked.cancel()
                try:
                    await blocked
                except asyncio.CancelledError:
                    pass
                else:
                    raise AssertionError("cancelled async request succeeded")
                await asyncio.wait_for(cancelled.wait(), 10)
                assert await echo_call(b"after cancellation", timeout=10) == b"after cancellation"
            completed = echo_call(b"completed", timeout=10)
            assert await completed == b"completed"
            for repeat in range(10):
                # Core rejects a second initial-metadata batch synchronously;
                # no completion callback will release its buffers.
                operations = (cygrpc.SendInitialMetadataOperation((("key", "value"),), 0),)
                try:
                    await cygrpc.execute_batch(completed._cython_call, operations,
                                               asyncio.get_running_loop())
                except cygrpc.ExecuteBatchError:
                    pass
                else:
                    raise AssertionError("duplicate initial metadata was accepted")
    finally:
        release.set()
        await server.stop(0)

asyncio.run(main())
print("async completion, concurrent RPCs, streaming, errors and cancellation passed")
'''
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", script],
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not result.stderr, result.stderr
    assert "errors and cancellation passed" in result.stdout


@pytest.mark.parametrize("enabled", [False, True])
def test_fork_managed_thread_lifetimes(enabled):
    script = '''
import os
import threading
from grpc._cython import cygrpc

enabled = os.environ["GRPC_ENABLE_FORK_SUPPORT"] == "1"
assert cygrpc.is_fork_support_enabled() == enabled
assert cygrpc.get_fork_epoch() == 0
counts = []
errors = []

def worker():
    counts.append(cygrpc._fork_state.active_thread_count._num_active_threads)

def failing_worker():
    worker()
    raise ValueError("intentional fork-thread failure")

previous_hook = threading.excepthook
threading.excepthook = errors.append
try:
    for callback in (worker, failing_worker):
        thread = cygrpc.ForkManagedThread(callback)
        thread.start()
        thread.join()
        assert cygrpc._fork_state.active_thread_count._num_active_threads == 0
finally:
    threading.excepthook = previous_hook
assert counts == [int(enabled), int(enabled)], counts
assert len(errors) == 1
assert errors[0].exc_type is ValueError
assert str(errors[0].exc_value) == "intentional fork-thread failure"
print("fork-managed thread normal and exceptional cleanup passed")
'''
    environment = dict(os.environ, GRPC_ENABLE_FORK_SUPPORT=str(int(enabled)))
    result = subprocess.run(
        [sys.executable, "-W", "error", "-c", script], env=environment,
        capture_output=True, text=True, timeout=60, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not result.stderr, result.stderr
    assert "normal and exceptional cleanup passed" in result.stdout


def test_distribution_license_metadata():
    """The installed wheel declares the linked components and ships each notice."""
    from importlib.metadata import distribution
    import hashlib
    from pathlib import Path

    dist = distribution("grpcio")
    assert dist.metadata["License-Expression"] == (
        "Apache-2.0 AND BSD-2-Clause AND BSD-3-Clause AND MIT"
    )
    assert dist.metadata.get("License") is None
    assert not any(value.startswith("License ::") for value in dist.metadata.get_all("Classifier", []))
    expected = {"LICENSE"} | {
        "rpm-licenses/" + name for name in (
            "grpcio-ABSEIL-LICENSE", "grpcio-UPB-LICENSE", "grpcio-UTF8-LICENSE",
            "grpcio-XXHASH-LICENSE", "grpcio-ADDRESS-LICENSE", "grpcio-license-sources.json",
        )
    }
    assert set(dist.metadata.get_all("License-File", [])) == expected
    files = [path for path in dist.files if ".dist-info/licenses/" in str(path)]
    assert len(files) == len(expected)
    for name in expected:
        installed = next(path for path in files if str(path).endswith("/licenses/" + name))
        original = Path(name)
        assert original.is_file(), name
        assert hashlib.sha256(installed.read_binary()).digest() == hashlib.sha256(original.read_bytes()).digest()
