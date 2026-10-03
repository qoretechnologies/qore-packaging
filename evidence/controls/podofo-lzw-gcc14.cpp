// Copyright 2026 Qore Technologies, s.r.o.; MIT.
#include <vector>
#include <cassert>
struct Item { std::vector<unsigned char> value; };
__attribute__((noinline)) void initialize(std::vector<Item>& table) {
    Item item;
    table.clear();
    table.reserve(4096);
    for (int i = 0; i <= 255; i++) {
        item.value.clear();
        item.value.push_back(static_cast<unsigned char>(i));
        table.push_back(item);
    }
    item.value.clear();
    table.push_back(item);
}
int main() {
    std::vector<Item> table;
    for (int repeat = 0; repeat < 10000; ++repeat) {
        initialize(table);
        assert(table.size() == 257 && table.back().value.empty());
        for (unsigned i = 0; i < 256; ++i) {
            assert(table[i].value.size() == 1 && table[i].value[0] == i);
        }
    }
}
