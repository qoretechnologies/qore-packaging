// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Reduced from QoreV8Program/QoreV8ProgramData's two reference counters and
// multiple inheritance. No Node or V8 code is involved.
#include <qore/Qore.h>
#include <cassert>
#include <cstddef>
#include <cstdio>

static unsigned destroyed;

class Program : public AbstractQoreProgramExternalData {
public:
    ~Program() override {
        assert(!weakRefs.reference_count());
        ++destroyed;
    }
    AbstractQoreProgramExternalData* copy(QoreProgram*) const override {
        return nullptr;
    }
    void doDeref() override {
        weakDeref();
    }
    bool weakDeref() {
        if (weakRefs.ROdereference()) {
            delete this;
            return true;
        }
        return false;
    }
private:
    QoreReferenceCounter weakRefs;
};

class ProgramData : public AbstractPrivateData, public Program {
public:
    void deref(ExceptionSink*) override {
        if (ROdereference()) {
            weakDeref();
        }
    }
    void deref() override {
        if (ROdereference()) {
            weakDeref();
        }
    }
private:
    ~ProgramData() override = default;
};

__attribute__((noinline)) static void release(ProgramData* value) {
    value->deref();
}

int main() {
    ProgramData* value = new ProgramData;
    auto* base = static_cast<Program*>(value);
    auto offset = reinterpret_cast<char*>(base) - reinterpret_cast<char*>(value);
    assert(offset == 16);
    std::printf("Program base offset: %td\n", offset);
    release(value);
    for (unsigned i = 0; i < 1000; ++i) {
        release(new ProgramData);
    }
    assert(destroyed == 1001);
}
