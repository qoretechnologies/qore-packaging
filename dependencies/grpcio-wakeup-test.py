# Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.
"""Exercise actual asyncio RPC completions while notification writes fail."""
import asyncio
import ctypes
import gc
import os
import sys
import grpc

mode = int(sys.argv[1])
assert mode in (1, 2, 3)
injector = ctypes.CDLL(None)
injector.grpcio_wakeup_arm.argtypes = [ctypes.c_int]
injector.grpcio_wakeup_arm.restype = None
for name in ('grpcio_wakeup_calls', 'grpcio_wakeup_failures'):
    getattr(injector, name).argtypes = []
    getattr(injector, name).restype = ctypes.c_uint

async def main():
    async def echo(value, context):
        return value
    server = grpc.aio.server()
    server.add_generic_rpc_handlers((grpc.method_handlers_generic_handler(
        'wakeup.Echo', {'Call': grpc.unary_unary_rpc_method_handler(echo)}),))
    port = server.add_insecure_port('127.0.0.1:0')
    assert port > 0
    await server.start()
    try:
        async with grpc.aio.insecure_channel(f'127.0.0.1:{port}') as channel:
            call = channel.unary_unary('/wakeup.Echo/Call')
            injector.grpcio_wakeup_arm(mode)
            try:
                async with asyncio.timeout(10):
                    for index in range(100):
                        value = f'wakeup {index}'.encode()
                        assert await call(value, timeout=5) == value
            except (TimeoutError, grpc.aio.AioRpcError) as error:
                # A baseline lost wakeup also prevents orderly async shutdown.
                # Report the specific failure and terminate this isolated control.
                print('FAIL: completion stranded:', repr(error),
                      'calls', injector.grpcio_wakeup_calls(),
                      'failures', injector.grpcio_wakeup_failures(), flush=True)
                os._exit(42)
    finally:
        injector.grpcio_wakeup_arm(0)
        await server.stop(None)

# Preserve counters before disarming for teardown.
original_arm = injector.grpcio_wakeup_arm
counts = {}
def arm(value):
    if value == 0:
        counts.update(calls=injector.grpcio_wakeup_calls(), failures=injector.grpcio_wakeup_failures())
    original_arm(value)
injector.grpcio_wakeup_arm = arm
asyncio.run(main())
gc.collect()
assert counts['calls'] > 0 and counts['failures'] > 0, counts
if mode == 1:
    assert counts['failures'] == 2, counts
else:
    assert counts['calls'] == counts['failures'], counts
print('PASS: 100 async RPCs under wakeup injection', mode, counts, flush=True)
