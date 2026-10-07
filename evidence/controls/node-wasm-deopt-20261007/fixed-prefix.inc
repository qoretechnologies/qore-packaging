base::OwnedVector<wasm::WasmDeoptEntry> GeneratorAdapter::Generate() {
  CHECK_EQ(result_, kSuccess);
  // Successful assembly assigns IDs from zero through kMaxNumberOfEntries.
  // Check this bound before narrowing the container size for serialization.
  CHECK_LE(deoptimization_exits_.size(),
           static_cast<size_t>(Deoptimizer::kMaxNumberOfEntries) + 1);
  int deopt_count = static_cast<int>(deoptimization_exits_.size());
  if (deopt_count == 0) {
    return {};
  }
  // Lazy deopts are not supported in wasm.
  DCHECK_EQ(lazy_deopt_count_, 0);
  // Wasm doesn't use the JS inlining handling via deopt info.
  DCHECK_EQ(inlined_function_count_, 0);

  auto deopt_entries =
      base::OwnedVector<wasm::WasmDeoptEntry>::New(deopt_count);
  // Populate deoptimization entries.
  for (int i = 0; i < deopt_count; i++) {
    const DeoptimizationExit* deoptimization_exit = deoptimization_exits_[i];
    CHECK_NOT_NULL(deoptimization_exit);
    CHECK_EQ(i, deoptimization_exit->deoptimization_id());
    deopt_entries[i] = {deoptimization_exit->bailout_id(),
                        deoptimization_exit->translation_id()};
  }

  return deopt_entries;
}
