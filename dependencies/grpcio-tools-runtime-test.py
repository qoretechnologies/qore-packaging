#!/usr/bin/env python3
# Copyright 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Exercise generated stubs against the distribution's installed gRPC runtime."""
from concurrent.futures import ThreadPoolExecutor
import unittest

import grpc
import simple_pb2
import simple_pb2_grpc


class Service(simple_pb2_grpc.SimpleMessageServiceServicer):
    def Tell(self, request, context):
        if not request.simple_msg.msg:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "message is required")
        return simple_pb2.SimpleMessageResponse(understood=request.simple_msg.msg == "Qore → gRPC")


class RuntimeTest(unittest.TestCase):
    def setUp(self):
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.addCleanup(self.executor.shutdown)
        self.server = grpc.server(self.executor)
        self.addCleanup(lambda: self.server.stop(0).wait())
        simple_pb2_grpc.add_SimpleMessageServiceServicer_to_server(Service(), self.server)
        port = self.server.add_insecure_port("127.0.0.1:0")
        self.assertGreater(port, 0)
        self.server.start()
        self.channel = grpc.insecure_channel(f"127.0.0.1:{port}")
        self.addCleanup(self.channel.close)
        self.stub = simple_pb2_grpc.SimpleMessageServiceStub(self.channel)

    def test_generated_stub_round_trip(self):
        message = simple_pb2.SimpleMessage(msg="Qore → gRPC", business=True)
        request = simple_pb2.SimpleMessageRequest(simple_msg=message)
        decoded = simple_pb2.SimpleMessageRequest.FromString(request.SerializeToString())
        self.assertEqual(message, decoded.simple_msg)
        self.assertEqual("business", decoded.simple_msg.WhichOneof("personal_or_business"))
        self.assertTrue(self.stub.Tell(decoded, timeout=10).understood)

    def test_generated_stub_propagates_failure(self):
        with self.assertRaises(grpc.RpcError) as raised:
            self.stub.Tell(simple_pb2.SimpleMessageRequest(), timeout=10)
        self.assertEqual(grpc.StatusCode.INVALID_ARGUMENT, raised.exception.code())
        self.assertEqual("message is required", raised.exception.details())


if __name__ == "__main__":
    unittest.main(verbosity=2)
