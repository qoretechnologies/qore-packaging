// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
'use strict';
const assert = require('node:assert/strict');
const names = ['years', 'yearsDisplay', 'months', 'monthsDisplay'];
const styles = [undefined, 'long', 'short', 'narrow'];
const displays = [undefined, 'auto', 'always'];
let cases = 0;
for (let repeat = 0; repeat < 4; ++repeat) {
  for (const style of ['long', 'short', 'narrow', 'digital']) {
    for (const years of styles) {
      for (const yearsDisplay of displays) {
        for (const months of styles) {
          for (const monthsDisplay of displays) {
            const values = [years, yearsDisplay, months, monthsDisplay];
            for (let fault = 0; fault <= 4; ++fault) {
              const options = {style};
              const visits = [];
              const failure = new Error('injected option getter failure');
              for (let i = 0; i < names.length; ++i) {
                Object.defineProperty(options, names[i], {
                  get() {
                    visits.push(names[i]);
                    if (fault === i + 1) {
                      throw failure;
                    }
                    return values[i];
                  }
                });
              }
              if (fault) {
                assert.throws(() => new Intl.DurationFormat('en', options),
                              error => error === failure);
                assert.deepEqual(visits, names.slice(0, fault));
              } else {
                const format = new Intl.DurationFormat('en', options);
                assert.deepEqual(visits, names);
                const result = format.resolvedOptions();
                const fallback = style === 'digital' ? 'short' : style;
                assert.equal(result.years, years ?? fallback);
                assert.equal(result.months, months ?? fallback);
                assert.equal(result.yearsDisplay, yearsDisplay ?? (years ? 'always' : 'auto'));
                assert.equal(result.monthsDisplay, monthsDisplay ?? (months ? 'always' : 'auto'));
                const duration = {years: 1, months: 2};
                const text = format.format(duration);
                assert(text.length > 0);
                assert.equal(format.formatToParts(duration).map(part => part.value).join(''), text);
              }
              ++cases;
            }
          }
        }
      }
    }
  }
  for (const property of names) {
    assert.throws(() => new Intl.DurationFormat('en', {[property]: 'invalid'}), RangeError);
    ++cases;
  }
}
console.log(`PASS: ${cases} actual Intl.DurationFormat construction, formatting and failure cases`);
