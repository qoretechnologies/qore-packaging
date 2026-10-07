// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const common = require('../common');
const dnstools = require('../common/dns');
const assert = require('assert');
const dns = require('dns');
const dgram = require('dgram');

// Keep both queries on a bound local fixture. An unreachable system resolver
// can complete a request synchronously, leaving no pending query to inspect.
const server = dgram.createSocket('udp4');
server.on('error', common.mustNotCall());
let completed = 0;
const answered = common.mustCall((err, addresses) => {
  assert.ifError(err);
  assert.deepStrictEqual(addresses, ['192.0.2.1']);
  if (++completed === 2) {
    server.close(common.mustCall());
  }
}, 2);
server.on('message', common.mustCall((message, { address, port }) => {
  const query = dnstools.parseDNSPacket(message);
  assert.strictEqual(query.questions.length, 1);
  assert.strictEqual(query.questions[0].domain, 'pending.example');
  assert.strictEqual(query.questions[0].type, 'A');
  server.send(dnstools.writeDNSPacket({
    id: query.id,
    questions: query.questions,
    answers: [{ domain: 'pending.example', type: 'A', ttl: 60, address: '192.0.2.1' }],
  }), port, address, common.mustCall((err) => assert.ifError(err)));
}, 2));
server.bind(0, '127.0.0.1', common.mustCall(() => {
  const local = [`127.0.0.1:${server.address().port}`];
  const resolver = new dns.Resolver();
  resolver.setServers(local);
  resolver.resolve4('pending.example', answered);
  assert.throws(() => resolver.setServers(local), {
    code: 'ERR_DNS_SET_SERVERS_FAILED',
    message: /^c-ares failed to set servers: "There are pending queries\." \[.+\]$/,
  });

  dns.setServers(local);
  dns.resolve4('pending.example', answered);
  // Replacing the default resolver remains allowed and must not cancel the
  // already active resolver's request.
  dns.setServers(local);
}));
