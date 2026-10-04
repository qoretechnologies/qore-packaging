// Copyright 2026 Qore Technologies, s.r.o.; Apache-2.0.
// DecodeSlow is adapted from gRPC's 2022 decode_huff_fuzzer.cc (Apache-2.0).
#include <arpa/inet.h>
#include <sys/un.h>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <optional>
#include <random>
#include <vector>
#include "src/core/ext/transport/chttp2/transport/decode_huff.h"
#include "src/core/ext/transport/chttp2/transport/huffsyms.h"
#include "src/core/lib/event_engine/tcp_socket_utils.h"

using Bytes = std::vector<uint8_t>;
using Decoded = std::optional<Bytes>;

Decoded DecodeSlow(const uint8_t* begin, const uint8_t* end) {
    uint64_t bits = 0;
    size_t left = 0;
    Bytes out;
    while (true) {
        while (begin != end && left < 30) {
            bits = (bits << 8) | *begin++;
            left += 8;
        }
        if (left < 5) {
            break;
        }
        bool found = false;
        for (int i = 0; i < GRPC_CHTTP2_NUM_HUFFSYMS; ++i) {
            const auto& sym = grpc_chttp2_huffsyms[i];
            if (sym.length > left) {
                continue;
            }
            if (((bits >> (left - sym.length)) & ((uint64_t{1} << sym.length) - 1)) == sym.bits) {
                found = true;
                left -= sym.length;
                if (i == 256) {
                    return out;
                }
                out.push_back(static_cast<uint8_t>(i));
                break;
            }
        }
        if (!found) {
            break;
        }
    }
    while (left > 0) {
        if ((bits & 1) == 0) {
            return std::nullopt;
        }
        bits >>= 1;
        --left;
    }
    return out;
}

Decoded DecodeFast(const Bytes& input) {
    Bytes out;
    auto sink = [&](uint8_t byte) { out.push_back(byte); };
    // Keep both endpoints valid even for an empty vector.
    const uint8_t empty = 0;
    const auto* begin = input.empty() ? &empty : input.data();
    if (!grpc_core::HuffDecoder<decltype(sink)>(sink, begin, begin + input.size()).Run()) {
        return std::nullopt;
    }
    return out;
}

void Compare(const Bytes& input) {
    const uint8_t empty = 0;
    const auto* begin = input.empty() ? &empty : input.data();
    assert(DecodeFast(input) == DecodeSlow(begin, begin + input.size()));
}

Bytes Encode(const Bytes& input) {
    Bytes out;
    uint8_t byte = 0;
    unsigned used = 0;
    for (auto value : input) {
        const auto& sym = grpc_chttp2_huffsyms[value];
        for (unsigned i = sym.length; i > 0; --i) {
            byte = static_cast<uint8_t>((byte << 1) | ((sym.bits >> (i - 1)) & 1));
            if (++used == 8) {
                out.push_back(byte);
                used = 0;
                byte = 0;
            }
        }
    }
    if (used != 0) {
        const unsigned pad = 8 - used;
        out.push_back(static_cast<uint8_t>((byte << pad) | ((1u << pad) - 1)));
    }
    return out;
}

void CheckAddresses() {
    using namespace grpc_event_engine::experimental;
    using Address = EventEngine::ResolvedAddress;
    for (uint32_t ip : {0u, 1u, 0x7f000001u, 0xc0000201u, 0xe0000001u, 0xffffffffu}) {
        for (uint16_t port : {0, 1, 443, 32768, 65535}) {
            sockaddr_in ipv4{};
            ipv4.sin_family = AF_INET;
            ipv4.sin_addr.s_addr = htonl(ip);
            ipv4.sin_port = htons(port);
            Address input(reinterpret_cast<const sockaddr*>(&ipv4), sizeof(ipv4));
            // Nonzero prior output detects stale scope/flow fields.
            sockaddr_in6 stale{};
            std::memset(&stale, 0xa5, sizeof(stale));
            stale.sin6_family = AF_INET6;
            Address mapped(reinterpret_cast<const sockaddr*>(&stale), sizeof(stale));
            assert(ResolvedAddressToV4Mapped(input, &mapped));
            assert(mapped.size() == sizeof(sockaddr_in6));
            const auto* result = reinterpret_cast<const sockaddr_in6*>(mapped.address());
            assert(result->sin6_family == AF_INET6);
            assert(result->sin6_port == ipv4.sin_port);
            assert(result->sin6_flowinfo == 0 && result->sin6_scope_id == 0);
            assert(IN6_IS_ADDR_V4MAPPED(&result->sin6_addr));
            assert(std::memcmp(result->sin6_addr.s6_addr + 12, &ipv4.sin_addr, 4) == 0);
            Address roundtrip;
            assert(ResolvedAddressIsV4Mapped(mapped, &roundtrip));
            assert(roundtrip.size() == sizeof(ipv4));
            assert(std::memcmp(roundtrip.address(), &ipv4, sizeof(ipv4)) == 0);
            assert(std::memcmp(input.address(), &ipv4, sizeof(ipv4)) == 0);
            const Address saved = mapped;
            assert(!ResolvedAddressToV4Mapped(saved, &mapped));
            assert(mapped.size() == saved.size());
            assert(std::memcmp(mapped.address(), saved.address(), saved.size()) == 0);
            sockaddr_un unix_address{};
            unix_address.sun_family = AF_UNIX;
            Address unsupported(reinterpret_cast<const sockaddr*>(&unix_address), sizeof(unix_address));
            assert(!ResolvedAddressToV4Mapped(unsupported, &mapped));
            assert(mapped.size() == saved.size());
            assert(std::memcmp(mapped.address(), saved.address(), saved.size()) == 0);
        }
    }
}

int main() {
    Compare({});
    for (unsigned a = 0; a < 256; ++a) {
        Compare({static_cast<uint8_t>(a)});
        for (unsigned b = 0; b < 256; ++b) {
            Compare({static_cast<uint8_t>(a), static_cast<uint8_t>(b)});
        }
        Bytes value{static_cast<uint8_t>(a)};
        assert(DecodeFast(Encode(value)) == Decoded(value));
    }
    std::mt19937 random(0x20261003);
    for (unsigned n = 0; n < 2000; ++n) {
        Bytes value(n % 129);
        for (auto& byte : value) {
            byte = static_cast<uint8_t>(random());
        }
        Compare(value);
        const auto encoded = Encode(value);
        Compare(encoded);
        assert(DecodeFast(encoded) == Decoded(value));
    }
    assert(!DecodeFast({0}));
    assert(!DecodeFast({0xff, 0x00}));
    CheckAddresses();
    std::puts("PASS: 65793 exhaustive short inputs, 4000 random/encoded inputs, 2256 roundtrips; 30 IPv4 mapping/negative cases");
}
