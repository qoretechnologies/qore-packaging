// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert = require('node:assert/strict');
const inspector = require('node:inspector');
const session = new inspector.Session();
session.connect();
const post = (method, params = {}) => new Promise((resolve, reject) => {
    session.post(method, params, (error, result) => error ? reject(error) : resolve(result));
});
(async () => {
    let checks = 0;
    try {
        await post('HeapProfiler.startSampling', {
            samplingInterval: 64,
            includeObjectsCollectedByMajorGC: true,
            includeObjectsCollectedByMinorGC: true,
        });
        const retained = [];
        for (let batch = 0; batch < 20; ++batch) {
            const objects = [];
            for (let i = 0; i < 1000; ++i) {
                const number = batch * 1000 + i + 0.25;
                const length = [1, 2, 7, 32][i % 4];
                objects.push({number, values: Array(length).fill(number), text: String(number).repeat(3)});
            }
            retained.push(objects[batch]);
            global.gc();
            for (let i = 0; i < objects.length; ++i) {
                const value = objects[i];
                const expected = batch * 1000 + i + 0.25;
                assert.equal(value.number, expected);
                assert.equal(value.values.length, [1, 2, 7, 32][i % 4]);
                for (const element of value.values) {
                    assert.equal(element, expected);
                }
                assert.equal(value.text, String(expected).repeat(3));
                ++checks;
            }
        }
        global.gc();
        for (let batch = 0; batch < retained.length; ++batch) {
            assert.equal(retained[batch].number, batch * 1001 + 0.25);
            ++checks;
        }
        const {profile} = await post('HeapProfiler.stopSampling');
        assert.ok(profile.samples.length > 0);
        assert.ok(profile.samples.every(sample => sample.size > 0));
        console.log(`PASS: ${checks} sampled allocation and post-GC lifetime cases`);
    } finally {
        session.disconnect();
    }
})().catch(error => {
    console.error(error);
    process.exitCode = 1;
});
