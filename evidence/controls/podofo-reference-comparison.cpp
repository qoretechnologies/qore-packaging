// Copyright 2026 Qore Technologies, s.r.o.; MIT.
#include <cassert>
#include <cstdint>
#include <memory>
#include <valgrind/memcheck.h>
struct Reference {
    uint8_t type;
    uint16_t generation;
    uint32_t object;
    Reference(uint32_t o, uint16_t g) : type(9), generation(g), object(o) {}
};
// Exact GCC 16 instruction used to test the high 48 bits of PdfReference.
// Its low 16 bits contain a tag and padding and cannot affect the result.
__attribute__((noinline)) bool indirect(const Reference& r) {
    bool result;
    asm("cmpq $65535, %1; seta %0" : "=qm"(result) : "m"(r) : "cc");
    return result;
}
int main() {
    for (unsigned i = 0; i < 100; ++i) {
        auto zero = std::make_unique<Reference>(0, 0);
        auto object = std::make_unique<Reference>(42, 0);
        auto generation = std::make_unique<Reference>(0, 42);
        VALGRIND_MAKE_MEM_UNDEFINED(reinterpret_cast<char*>(zero.get()) + 1, 1);
        assert(!indirect(*zero));
        assert(indirect(*object));
        assert(indirect(*generation));
    }
}
