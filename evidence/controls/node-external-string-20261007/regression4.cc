// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <v8.h>
#include <libplatform/libplatform.h>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <string>
#include <cstring>
#include <vector>
#include <dlfcn.h>
static unsigned disposed = 0;
static void check(bool ok, const char* what, int line) { if (!ok) { std::fprintf(stderr, "line %d: %s\n", line, what); std::abort(); } }
#define require(x) check((x), #x, __LINE__)
class One final : public v8::String::ExternalOneByteStringResource {
 public:
  explicit One(std::string value) : value_(std::move(value)) {}
  ~One() override { ++disposed; }
  const char* data() const override { return value_.data(); }
  size_t length() const override { return value_.size(); }
 private: std::string value_;
};
class Two final : public v8::String::ExternalStringResource {
 public:
  explicit Two(std::vector<uint16_t> value) : value_(std::move(value)) {}
  ~Two() override { ++disposed; }
  const uint16_t* data() const override { return value_.data(); }
  size_t length() const override { return value_.size(); }
 private: std::vector<uint16_t> value_;
};
int main(int argc, char** argv) {
    require(argc == 2 || argc == 3);
    const bool shared = std::strcmp(argv[1], "shared") == 0;
    const bool negative = argc == 3;
    if (shared) { v8::V8::SetFlagsFromString("--shared-string-table"); }
    auto platform = v8::platform::NewDefaultPlatform();
    v8::V8::InitializePlatform(platform.get());
    require(v8::V8::Initialize());
    auto allocator = std::unique_ptr<v8::ArrayBuffer::Allocator>(v8::ArrayBuffer::Allocator::NewDefaultAllocator());
    v8::Isolate::CreateParams params; params.array_buffer_allocator = allocator.get();
    auto* isolate = v8::Isolate::New(params);
    // The RPM is Release. Invoke its exported verifier with the native member
    // receiver ABI to exercise the same checks that V8_ENABLE_CHECKS clients use.
    using Verify = void (*)(const v8::String*, v8::String::ExternalStringResource*);
    auto verify = reinterpret_cast<Verify>(dlsym(RTLD_DEFAULT, "_ZNK2v86String28VerifyExternalStringResourceEPNS0_22ExternalStringResourceE"));
    require(verify != nullptr);
    unsigned checks = 0;
    {
        v8::Isolate::Scope scope(isolate);
        v8::HandleScope handles(isolate);
        auto context = v8::Context::New(isolate);
        v8::Context::Scope entered(context);
        for (unsigned n = 0; n < 100; ++n) {
            for (auto kind : {v8::NewStringType::kNormal, v8::NewStringType::kInternalized}) {
                const std::string text = "external-forwarding-resource-0123456789-" + std::to_string(n)
                    + (kind == v8::NewStringType::kNormal ? "-normal" : "-internalized");
                auto str = v8::String::NewFromUtf8(isolate, text.c_str(), kind).ToLocalChecked();
                require(!str->IsExternal());
                verify(*str, nullptr);
                auto resource = std::make_unique<One>(text);
                auto* expected = resource.get();
                if (kind == v8::NewStringType::kNormal) {
                    str = v8::String::NewExternalOneByte(isolate, resource.get()).ToLocalChecked();
                } else {
                    require(str->MakeExternal(resource.get()));
                }
                resource.release();
                require(str->IsExternalOneByte());
                require(str->GetExternalOneByteStringResource() == expected);
                require(str->GetExternalStringResource() == nullptr);
                verify(*str, nullptr);
                v8::String::Utf8Value result(isolate, str);
                require(*result != nullptr && std::string(*result, result.length()) == text);
                ++checks;

                std::vector<uint16_t> wide(text.begin(), text.end());
                wide.push_back(0x100); wide.push_back(0x20ac);
                auto wstr = v8::String::NewFromTwoByte(isolate,
                    wide.data(), kind, static_cast<int>(wide.size())).ToLocalChecked();
                require(!wstr->IsExternal());
                verify(*wstr, nullptr);
                auto wresource = std::make_unique<Two>(wide);
                auto* wexpected = wresource.get();
                if (kind == v8::NewStringType::kNormal) {
                    wstr = v8::String::NewExternalTwoByte(isolate, wresource.get()).ToLocalChecked();
                } else {
                    require(wstr->MakeExternal(wresource.get()));
                }
                wresource.release();
                require(wstr->IsExternalTwoByte());
                require(wstr->GetExternalStringResource() == wexpected);
                verify(*wstr, negative ? nullptr : wexpected);
                v8::String::Value wresult(isolate, wstr);
                require(wresult.length() == static_cast<uint32_t>(wide.size()));
                require(std::memcmp(*wresult, wide.data(), wide.size() * sizeof(uint16_t)) == 0);
                ++checks;
            }
        }
    }
    isolate->Dispose();
    v8::V8::Dispose();
    v8::V8::DisposePlatform();
    require(disposed == 400);
    std::printf("PASS: %u native string lifetimes, both encodings and storage modes; %u resources disposed\n", checks, disposed);
}
