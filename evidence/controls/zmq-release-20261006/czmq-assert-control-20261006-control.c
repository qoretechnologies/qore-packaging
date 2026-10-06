/* Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT */
#include "zhashx.c"

int main(void) {
    zhashx_t *table = zhashx_new();
    if (!table) { return 2; }
    size_t initial = primes[table->prime_index];
    int values[10000];
    for (int i = 0; i < 10000; ++i) {
        char key[40];
        snprintf(key, sizeof(key), "record-%d", i);
        values[i] = i;
        if (zhashx_insert(table, key, &values[i]) != 0) { return 3; }
    }
    size_t grown = primes[table->prime_index];
    for (int i = 0; i < 10000; ++i) {
        char key[40];
        snprintf(key, sizeof(key), "record-%d", i);
        if (zhashx_lookup(table, key) != &values[i]) { return 4; }
        zhashx_delete(table, key);
    }
    if (zhashx_size(table) != 0) { return 5; }
    size_t emptied = primes[table->prime_index];
    zhashx_destroy(&table);
    if (table) { return 6; }
    printf("10000 insert/lookup/delete lifetimes: initial buckets=%zu; grown=%zu; emptied=%zu\n",
        initial, grown, emptied);
    if (grown <= initial) {
        fprintf(stderr, "release configuration removed mandatory hash-table resizing\n");
        return 7;
    }
    return 0;
}
