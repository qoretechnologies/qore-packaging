// Copyright 2012 the V8 project authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

#include "src/api/api.h"

#include <algorithm>  // For min
#include <cmath>      // For isnan.
#include <limits>
#include <optional>
#include <sstream>
#include <string>
#include <utility>  // For move
#include <vector>

#include "include/v8-array-buffer.h"
#include "include/v8-callbacks.h"
#include "include/v8-cppgc.h"
#include "include/v8-date.h"
#include "include/v8-embedder-state-scope.h"
#include "include/v8-extension.h"
#include "include/v8-external-memory-accounter.h"
#include "include/v8-fast-api-calls.h"
#include "include/v8-function.h"
#include "include/v8-json.h"
#include "include/v8-locker.h"
#include "include/v8-primitive-object.h"
#include "include/v8-profiler.h"
#include "include/v8-source-location.h"
#include "include/v8-template.h"
#include "include/v8-unwinder-state.h"
#include "include/v8-util.h"
#include "include/v8-wasm.h"
#include "src/api/api-arguments.h"
#include "src/api/api-inl.h"
#include "src/api/api-natives.h"
#include "src/base/hashing.h"
#include "src/base/logging.h"
#include "src/base/platform/memory.h"
#include "src/base/platform/platform.h"
#include "src/base/platform/time.h"
#include "src/base/safe_conversions.h"
#include "src/base/utils/random-number-generator.h"
#include "src/base/vector.h"
#include "src/builtins/accessors.h"
#include "src/builtins/builtins-utils.h"
#include "src/codegen/compilation-cache.h"
#include "src/codegen/compiler.h"
#include "src/codegen/cpu-features.h"
#include "src/codegen/script-details.h"
#include "src/common/assert-scope.h"
#include "src/common/globals.h"
#include "src/compiler-dispatcher/lazy-compile-dispatcher.h"
#include "src/date/date.h"
#include "src/debug/debug.h"
#include "src/deoptimizer/deoptimizer.h"
#include "src/execution/embedder-state.h"
#include "src/execution/execution.h"
#include "src/execution/frames-inl.h"
#include "src/execution/isolate-inl.h"
#include "src/execution/messages.h"
#include "src/execution/microtask-queue.h"
#include "src/execution/simulator.h"
#include "src/execution/v8threads.h"
#include "src/execution/vm-state-inl.h"
#include "src/handles/global-handles.h"
#include "src/handles/persistent-handles.h"
#include "src/handles/shared-object-conveyor-handles.h"
#include "src/handles/traced-handles-inl.h"
#include "src/heap/heap-inl.h"
#include "src/heap/heap-layout-inl.h"
#include "src/heap/heap-write-barrier.h"
#include "src/heap/safepoint.h"
#include "src/heap/visit-object.h"
#include "src/init/bootstrapper.h"
#include "src/init/icu_util.h"
#include "src/init/startup-data-util.h"
#include "src/init/v8.h"
#include "src/json/json-parser.h"
#include "src/json/json-stringifier.h"
#include "src/logging/counters-scopes.h"
#include "src/logging/metrics.h"
#include "src/logging/runtime-call-stats-scope.h"
#include "src/logging/tracing-flags.h"
#include "src/numbers/conversions-inl.h"
#include "src/objects/api-callbacks.h"
#include "src/objects/backing-store.h"
#include "src/objects/contexts.h"
#include "src/objects/embedder-data-array-inl.h"
#include "src/objects/embedder-data-slot-inl.h"
#include "src/objects/hash-table-inl.h"
#include "src/objects/heap-object.h"
#include "src/objects/instance-type-inl.h"
#include "src/objects/instance-type.h"
#include "src/objects/js-array-buffer-inl.h"
#include "src/objects/js-array-inl.h"
#include "src/objects/js-collection-inl.h"
#include "src/objects/js-objects.h"
#include "src/objects/js-promise-inl.h"
#include "src/objects/js-regexp-inl.h"
#include "src/objects/js-weak-refs-inl.h"
#include "src/objects/module-inl.h"
#include "src/objects/objects-inl.h"
#include "src/objects/oddball.h"
#include "src/objects/ordered-hash-table-inl.h"
#include "src/objects/primitive-heap-object.h"
#include "src/objects/property-descriptor.h"
#include "src/objects/property-details.h"
#include "src/objects/property.h"
#include "src/objects/prototype.h"
#include "src/objects/shared-function-info.h"
#include "src/objects/slots.h"
#include "src/objects/smi.h"
#include "src/objects/string.h"
#include "src/objects/synthetic-module-inl.h"
#include "src/objects/templates.h"
#include "src/objects/value-serializer.h"
#include "src/parsing/parse-info.h"
#include "src/parsing/parser.h"
#include "src/parsing/pending-compilation-error-handler.h"
#include "src/parsing/scanner-character-streams.h"
#include "src/profiler/cpu-profiler.h"
#include "src/profiler/heap-profiler.h"
#include "src/profiler/heap-snapshot-generator-inl.h"
#include "src/profiler/profile-generator-inl.h"
#include "src/profiler/tick-sample.h"
#include "src/regexp/regexp-utils.h"
#include "src/roots/static-roots.h"
#include "src/runtime/runtime.h"
#include "src/sandbox/external-pointer.h"
#include "src/sandbox/isolate.h"
#include "src/sandbox/sandbox.h"
#include "src/snapshot/code-serializer.h"
#include "src/snapshot/embedded/embedded-data.h"
#include "src/snapshot/snapshot.h"
#include "src/strings/char-predicates-inl.h"
#include "src/strings/string-hasher.h"
#include "src/strings/unicode-inl.h"
#include "src/tracing/trace-event.h"
#include "src/utils/detachable-vector.h"
#include "src/utils/identity-map.h"
#include "src/utils/version.h"

#if V8_ENABLE_WEBASSEMBLY
#include "src/debug/debug-wasm-objects.h"
#include "src/trap-handler/trap-handler.h"
#include "src/wasm/streaming-decoder.h"
#include "src/wasm/value-type.h"
#include "src/wasm/wasm-engine.h"
#include "src/wasm/wasm-js.h"
#include "src/wasm/wasm-objects-inl.h"
#include "src/wasm/wasm-result.h"
#include "src/wasm/wasm-serialization.h"
#endif  // V8_ENABLE_WEBASSEMBLY

#if V8_OS_LINUX || V8_OS_DARWIN || V8_OS_FREEBSD
#include <signal.h>
#include <unistd.h>

#if V8_ENABLE_WEBASSEMBLY
#include "include/v8-wasm-trap-handler-posix.h"
#include "src/trap-handler/handler-inside-posix.h"
#endif  // V8_ENABLE_WEBASSEMBLY

#endif  // V8_OS_LINUX || V8_OS_DARWIN || V8_OS_FREEBSD

#if V8_OS_WIN
#include "include/v8-wasm-trap-handler-win.h"
#include "src/trap-handler/handler-inside-win.h"
#if defined(V8_OS_WIN64)
#include "src/base/platform/wrappers.h"
#include "src/diagnostics/unwinding-info-win64.h"
#endif  // V8_OS_WIN64
#endif  // V8_OS_WIN

#if defined(V8_ENABLE_ETW_STACK_WALKING)
#include "src/diagnostics/etw-jit-win.h"
#endif  // V8_ENABLE_ETW_STACK_WALKING

// Has to be the last include (doesn't have include guards):
#include "src/api/api-macros.h"

namespace v8 {
namespace {
// Test adapter: the public getter accesses this same forwarding table in the
// packaged runtime. Hidden isolate globals prevent linking the internal helper
// from an executable into the distribution's shared libnode.
v8::String::ExternalStringResourceBase* GetExternalResourceFromForwardingTable(
    const v8::String* api_string, i::Tagged<i::String>, uint32_t, bool* is_one_byte) {
  v8::String::Encoding encoding;
  auto resource = api_string->GetExternalStringResourceBase(v8::Isolate::GetCurrent(), &encoding);
  *is_one_byte = encoding == v8::String::ONE_BYTE_ENCODING;
  return resource;
}

}
void v8::String::VerifyExternalStringResource(
    v8::String::ExternalStringResource* value) const {
  i::DisallowGarbageCollection no_gc;
  i::Tagged<i::String> str = *Utils::OpenDirectHandle(this);
  const v8::String::ExternalStringResource* expected;

  if (i::IsThinString(str)) {
    str = i::Cast<i::ThinString>(str)->actual();
  }

  if (i::StringShape(str).IsExternalTwoByte()) {
    const void* resource = i::Cast<i::ExternalTwoByteString>(str)->resource();
    expected = reinterpret_cast<const ExternalStringResource*>(resource);
  } else {
    uint32_t raw_hash_field = str->raw_hash_field(kAcquireLoad);
    if (i::String::IsExternalForwardingIndex(raw_hash_field)) {
      bool is_one_byte;
      auto resource = GetExternalResourceFromForwardingTable(
          this, str, raw_hash_field, &is_one_byte);
      if (!is_one_byte) {
        expected = reinterpret_cast<const ExternalStringResource*>(resource);
      }
    } else {
      expected = nullptr;
    }
  }
  CHECK_EQ(expected, value);
}

}
