# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import difflib, hashlib, json

root = Path('results/leap-nodejs24-obs-flags-candidate9-20261007/rpmbuild/BUILD/nodejs24-libnode-24.18.1-build/node-v24.18.1/deps/v8')
out = Path('work/node-wasm-deopt-review-20261007')
proposed = out / 'proposed'
p = proposed / 'src/deoptimizer/deoptimizer.cc'
s = p.read_text()
anchor = '''} else if (!Is64() && liftoff_iter->is_gp_reg_pair()) {
          intptr_t reg_value = kZapValue;
          switch (value.kind()) {
            case TranslatedValue::Kind::kInt32:
'''
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + '              CHECK_EQ(liftoff_iter->kind(), wasm::ValueKind::kI64);\n')
anchor = '''          case wasm::ValueKind::kS128: {
            int64x2 values = value.simd_value().to_i64x2();'''
assert s.count(anchor) == 1
s = s.replace(anchor, '''          case wasm::ValueKind::kS128: {
            CHECK_EQ(value.kind(), TranslatedValue::Kind::kSimd128);
            int64x2 values = value.simd_value().to_i64x2();''')
p.write_text(s)
p = proposed / 'src/compiler/backend/code-generator.cc'
s = p.read_text()
anchor = '''base::OwnedVector<uint8_t> CodeGenerator::GenerateWasmDeoptimizationData() {
  CHECK_EQ(result_, kSuccess);
'''
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + '''  // Successful assembly assigns IDs from zero through kMaxNumberOfEntries.
  // Check this bound before narrowing the container size for serialization.
  CHECK_LE(deoptimization_exits_.size(),
           static_cast<size_t>(Deoptimizer::kMaxNumberOfEntries) + 1);
''')
p.write_text(s)
meta = json.loads((out / 'commit.txt').read_text()[4:])
patch = '''# Copyright 2026 Qore Technologies, s.r.o.
# Backport V8 a548b49ac38290fa2cf449117e19f872d0f3c7f5 (BSD-3-Clause).
# Preserve code-generation failure and deoptimization metadata invariants.
# Adapt the pre-Simd128-register API and check the count before narrowing.
'''
for f in meta['tree_diff']:
    path = f['new_path']
    patch += ''.join(difflib.unified_diff((root / path).read_text().splitlines(True),
        (proposed / path).read_text().splitlines(True),
        fromfile='a/deps/v8/' + path, tofile='b/deps/v8/' + path))
(out / 'proposed.patch').write_text(patch)
extracts = []
for variant, source in [('original', root), ('fixed', proposed)]:
    s = (source / 'src/compiler/backend/code-generator.cc').read_text()
    a = s.index('base::OwnedVector<uint8_t> CodeGenerator::GenerateWasmDeoptimizationData() {')
    b = s.index('  base::Vector<const uint8_t> frame_translations =', a)
    body = s[a:b]
    extracts.append(dict(variant=variant, file='src/compiler/backend/code-generator.cc',
        line=s[:a].count('\n')+1, body=body, sha256=hashlib.sha256(body.encode()).hexdigest()))
    body = body.replace('base::OwnedVector<uint8_t> CodeGenerator::GenerateWasmDeoptimizationData()',
                        'base::OwnedVector<wasm::WasmDeoptEntry> GeneratorAdapter::Generate()')
    (out / (variant + '-prefix.inc')).write_text(body + '  return deopt_entries;\n}\n')
(out / 'source-extracts.json').write_text(json.dumps(extracts, indent=2) + '\n')
(out / 'control.cc').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <cstdio>
#include <cstring>
#include <vector>
#include "src/wasm/wasm-deopt-data.h"
#include "src/objects/deoptimization-data.h"
#include "src/deoptimizer/deoptimizer.h"
#include "src/zone/accounting-allocator.h"
namespace v8::internal {
// Only the surrounding generator state is adapted. The allocation/fill prefix,
// OwnedVector, BytecodeOffset, serialized entries and serializer are unchanged.
struct DeoptimizationExit {
  int id;
  int deoptimization_id() const { return id; }
  BytecodeOffset bailout_id() const { return BytecodeOffset(id * 3); }
  int translation_id() const { return id * 5; }
};
struct GeneratorAdapter {
  enum Result { kSuccess, kTooManyDeoptimizationBailouts };
  Result result_ = kSuccess;
  int lazy_deopt_count_ = 0;
  int inlined_function_count_ = 0;
  std::vector<DeoptimizationExit*> deoptimization_exits_;
  base::OwnedVector<wasm::WasmDeoptEntry> Generate();
};
#include PREFIX_FILE
}  // namespace v8::internal
namespace i = v8::internal;
namespace w = v8::internal::wasm;
int main(int argc, char** argv) {
  const char* mode = argc == 2 ? argv[1] : "positive";
  i::AccountingAllocator allocator;
  i::Zone zone(&allocator, "Wasm metadata bounds regression");
  i::ZoneDeque<i::DeoptimizationLiteral> literals(&zone);
  literals.emplace_back(int32_t(-17));
  literals.emplace_back(int64_t(-1234567890123LL));
  literals.emplace_back(uint64_t(0xfedcba9876543210ULL));
  literals.emplace_back(3.25);
  i::GeneratorAdapter generator;
  if (!std::strcmp(mode, "failed-generation")) {
    generator.result_ = i::GeneratorAdapter::kTooManyDeoptimizationBailouts;
    auto entries = generator.Generate();
    CHECK(entries.empty());
    return 0;
  }
  if (!std::strcmp(mode, "excess-count") || !std::strcmp(mode, "duplicate-id")) {
    size_t count = !std::strcmp(mode, "excess-count") ? 16386 : 2;
    std::vector<i::DeoptimizationExit> exits(count);
    for (size_t n = 0; n < count; ++n) {
      exits[n].id = !std::strcmp(mode, "duplicate-id") ? 0 : static_cast<int>(n);
      generator.deoptimization_exits_.push_back(&exits[n]);
    }
    auto entries = generator.Generate();
    CHECK_EQ(entries.size(), count);
    return 0;
  }
  if (!std::strcmp(mode, "negative-count") || !std::strcmp(mode, "mismatched-count")) {
    auto entries = v8::base::OwnedVector<w::WasmDeoptEntry>::New(1);
    const uint8_t translation[] = {1, 2, 3};
    auto bytes = w::WasmDeoptDataProcessor::Serialize(0,
        !std::strcmp(mode, "negative-count") ? -1 : 2,
        v8::base::VectorOf(translation), v8::base::VectorOf(entries), literals);
    CHECK_GT(bytes.size(), 0);
    return 0;
  }
  if (!std::strcmp(mode, "out-of-range")) {
    // Two backing entries keep the baseline read defined, but only one belongs
    // to the logical table. The corrected view must reject index one.
    auto entries = v8::base::OwnedVector<w::WasmDeoptEntry>::New(2);
    const uint8_t translation[] = {1, 2, 3};
    auto bytes = w::WasmDeoptDataProcessor::Serialize(0, 2,
        v8::base::VectorOf(translation), v8::base::VectorOf(entries), literals);
    w::WasmDeoptData header;
    std::memcpy(&header, bytes.begin(), sizeof(header));
    header.entry_count = 1;
    std::memcpy(bytes.begin(), &header, sizeof(header));
    w::WasmDeoptView view(v8::base::VectorOf(bytes));
    CHECK_EQ(view.GetDeoptEntry(1).translation_index, -1);
    return 0;
  }
  CHECK_EQ(std::strcmp(mode, "positive"), 0);
  size_t checks = 0;
  for (unsigned repeat = 0; repeat < 10; ++repeat) {
    for (int count : {0, 1, 2, 17, 16384, 16385}) {
      std::vector<i::DeoptimizationExit> exits(count);
      generator.deoptimization_exits_.clear();
      for (int n = 0; n < count; ++n) {
        exits[n].id = n;
        generator.deoptimization_exits_.push_back(&exits[n]);
      }
      auto entries = generator.Generate();
      CHECK_EQ(entries.size(), static_cast<size_t>(count));
      // Nonempty pointer for a zero-length span keeps memcpy preconditions.
      const uint8_t translation[] = {0, 127, 128, 255, 42};
      w::WasmDeoptEntry empty;
      auto entry_span = count ? v8::base::VectorOf(entries) : v8::base::VectorOf(&empty, 0);
      for (size_t length : {0, 1, 5}) {
        auto bytes = w::WasmDeoptDataProcessor::Serialize(17, count,
            v8::base::VectorOf(translation, length), entry_span, literals);
        w::WasmDeoptView view(v8::base::VectorOf(bytes));
        CHECK(view.HasDeoptData());
        auto data = view.GetDeoptData();
        CHECK_EQ(data.entry_count, count);
        CHECK_EQ(data.eager_deopt_count, count);
        CHECK_EQ(data.deopt_exit_start_offset, 17);
        CHECK_EQ(data.translation_array_size, length);
        CHECK_EQ(data.deopt_literals_size, literals.size());
        CHECK_EQ(std::memcmp(view.GetTranslationsArray().begin(), translation, length), 0);
        for (int n = 0; n < count; ++n) {
          auto entry = view.GetDeoptEntry(n);
          CHECK_EQ(entry.bytecode_offset, i::BytecodeOffset(n * 3));
          CHECK_EQ(entry.translation_index, n * 5);
          checks += 2;
        }
        auto restored = view.BuildDeoptimizationLiteralArray();
        CHECK_EQ(restored.size(), literals.size());
        for (size_t n = 0; n < literals.size(); ++n) {
          CHECK(restored[n] == literals[n]);
          ++checks;
        }
        checks += 8;
      }
    }
  }
  std::printf("PASS: %zu allocation, metadata round-trip and boundary checks\n", checks);
}
''')
print('Prepared upstream backport, explicit count invariant, real-type metadata controls.')
