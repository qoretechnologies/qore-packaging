// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "node.h"
#include "uv.h"
#include <cassert>
#include <charconv>
#include <cstdio>
#include <memory>
#include <string>
#include <vector>

extern "C" unsigned int qore_detached_thread_count();

static int execute(node::CommonEnvironmentSetup& setup) {
    v8::Locker locker(setup.isolate());
    v8::Isolate::Scope isolate_scope(setup.isolate());
    v8::HandleScope handles(setup.isolate());
    v8::Context::Scope context(setup.context());
    auto loaded = node::LoadEnvironment(setup.env(),
        "const assert = require('node:assert/strict');"
        "assert.equal(require('node:inspector').url(), undefined);");
    if (loaded.IsEmpty()) {
        return 1;
    }
    return node::SpinEventLoop(setup.env()).FromMaybe(1);
}

int main(int argc, char** argv) {
    if (argc != 3 || (std::string(argv[1]) != "serial" &&
                      std::string(argv[1]) != "concurrent")) {
        return 2;
    }
    const std::string argument(argv[2]);
    int repeats = 0;
    const auto parsed = std::from_chars(argument.data(), argument.data() + argument.size(), repeats);
    if (parsed.ec != std::errc() || parsed.ptr != argument.data() + argument.size()
            || repeats < 1 || repeats > 1000) {
        return 2;
    }
    auto initialization = node::InitializeOncePerProcess({"node-inspector-control"}, {
        node::ProcessInitializationFlags::kNoInitializeV8,
        node::ProcessInitializationFlags::kNoInitializeNodeV8Platform});
    assert(!initialization->early_return());
    assert(initialization->errors().empty());
    auto platform = node::MultiIsolatePlatform::Create(2);
    v8::V8::InitializePlatform(platform.get());
    assert(v8::V8::Initialize());
    unsigned int first = 0;
    int result = 0;
    for (int iteration = 0; iteration < repeats; ++iteration) {
        std::vector<std::string> errors;
        auto setup = node::CommonEnvironmentSetup::Create(
            platform.get(), &errors, initialization->args(), initialization->exec_args());
        assert(setup && errors.empty());
        if (std::string(argv[1]) == "concurrent") {
            auto second = node::CommonEnvironmentSetup::Create(
                platform.get(), &errors, initialization->args(), initialization->exec_args());
            assert(second && errors.empty());
            result |= execute(*second);
        }
        result |= execute(*setup);
        setup.reset();
        unsigned int count = qore_detached_thread_count();
        std::printf("environment %d: detached thread creations = %u\n", iteration + 1, count);
        std::fflush(stdout);
        if (iteration == 0) {
            first = count;
            if (first != 1) {
                result = 1;
            }
        } else if (count != first) {
            result = 1;
        }
    }
    v8::V8::Dispose();
    v8::V8::DisposePlatform();
    platform.reset();
    node::TearDownOncePerProcess();
    return result;
}
