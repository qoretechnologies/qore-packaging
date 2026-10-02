# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
"""Verify a non-loopback interface and the absence of an external route."""
import errno
import fcntl
import ipaddress
from pathlib import Path
import socket
import struct

addresses = []
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as control:
    for _, name in socket.if_nameindex():
        if name == "lo":
            continue
        data = fcntl.ioctl(control, 0x8915, struct.pack("256s", name.encode()))
        ip = socket.inet_ntoa(data[20:24])
        assert not ipaddress.ip_address(ip).is_loopback
        addresses.append(ip)
assert addresses, "no non-loopback IPv4 interface"
routes = Path("/proc/net/route").read_text()
print(routes)
assert not any(row.split()[1] == "00000000" for row in routes.splitlines()[1:]), "unexpected default route"
for ip in addresses:
    with socket.socket() as listener, socket.socket() as client:
        listener.settimeout(3)
        client.settimeout(3)
        listener.bind(("0.0.0.0", 0))
        listener.listen()
        client.connect((ip, listener.getsockname()[1]))
        with listener.accept()[0] as peer:
            peer.settimeout(3)
            client.sendall(b"offline")
            client.shutdown(socket.SHUT_WR)
            with peer.makefile("rb") as incoming:
                assert incoming.read() == b"offline"
with socket.socket() as client:
    client.settimeout(1)
    result = client.connect_ex(("192.0.2.1", 80))
    assert result == errno.ENETUNREACH, result
print("Non-loopback bind/connect works; external destination fails immediately with ENETUNREACH")
