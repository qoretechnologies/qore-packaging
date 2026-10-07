// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
// This tests heap snapshot integration of dns ChannelWrap.
const common = require('../common');
const { validateByRetainingPath } = require('../common/heap');
const assert = require('assert');

// Before dns is loaded, no ChannelWrap should be created.
assert.strictEqual(validateByRetainingPath('Node / ChannelWrap', []).length, 0);
const dns = require('dns');
validateByRetainingPath('Node / ChannelWrap', [
  { node_name: 'ChannelWrap', edge_name: 'native_to_javascript' },
]);

const dgram = require('dgram');
const dnstools = require('../common/dns');
const server = dgram.createSocket('udp4');
server.on('error', common.mustNotCall());
server.bind(0, '127.0.0.1', common.mustCall(() => {
  dns.setServers([`127.0.0.1:${server.address().port}`]);
  dns.resolve4('pending.example', common.mustCall((err, addresses) => {
    assert.ifError(err);
    assert.deepStrictEqual(addresses, ['192.0.2.1']);
    server.close(common.mustCall());
  }));
  // The local server cannot respond before this synchronous snapshot completes.
  validateByRetainingPath('Node / ChannelWrap', [
    { node_name: 'Node / NodeAresTask::List', edge_name: 'task_list' },
  ]);
}));
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
}));
