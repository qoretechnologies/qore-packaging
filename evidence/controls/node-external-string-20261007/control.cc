// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <v8.h>
#include <libplatform/libplatform.h>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <string>
#include <cstring>
static unsigned disposed = 0;
static void require(bool ok) { if (!ok) { std::abort(); } }
class One final : public v8::String::ExternalOneByteStringResource {
 public:
  explicit One(std::string value) : value_(std::move(value)) {}
  ~One() override { ++disposed; }
  const char* data() const override { return value_.data(); }
  size_t length() const override { return value_.size(); }
 private: std::string value_;
};
int main(int argc, char** argv) {
    require(argc == 2);
    const bool shared = std::strcmp(argv[1], "shared") == 0;
    if (shared) { v8::V8::SetFlagsFromString("--shared-string-table"); }
    auto platform = v8::platform::NewDefaultPlatform();
    v8::V8::InitializePlatform(platform.get());
    require(v8::V8::Initialize());
    auto allocator = std::unique_ptr<v8::ArrayBuffer::Allocator>(v8::ArrayBuffer::Allocator::NewDefaultAllocator());
    v8::Isolate::CreateParams params; params.array_buffer_allocator = allocator.get();
    auto* isolate = v8::Isolate::New(params);
    {
        v8::Isolate::Scope scope(isolate);
        v8::HandleScope handles(isolate);
        auto context = v8::Context::New(isolate);
        v8::Context::Scope entered(context);
        const std::string text = "external-string-forwarding-control-0123456789";
        auto str = v8::String::NewFromUtf8(isolate, text.c_str(), v8::NewStringType::kInternalized).ToLocalChecked();
        auto resource = std::make_unique<One>(text);
        require(str->MakeExternal(resource.get()));
        resource.release();
        require(str->IsExternalOneByte());
        require(str->GetExternalOneByteStringResource() != nullptr);
        std::printf("one-byte resource established (%s)\n", shared ? "shared" : "ordinary"); std::fflush(stdout);
        // The public API promises nullptr for a one-byte resource. In checking
        // clients this also calls VerifyExternalStringResource(nullptr).
        require(str->GetExternalStringResource() == nullptr);
        v8::String::Utf8Value result(isolate, str);
        require(*result != nullptr && std::string(*result, result.length()) == text);
    }
    isolate->Dispose();
    v8::V8::Dispose();
    v8::V8::DisposePlatform();
    require(disposed == 1);
    std::puts("PASS: resource type, contents and disposal");
}
