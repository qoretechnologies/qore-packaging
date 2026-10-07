// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
void require(bool b) {if(!b) {std::abort();}}
Flags v8_flags{};
unsigned no_gc_depth=0;
__attribute__((noinline))
void CompleteArrayBufferSweeping(Heap* heap) {
  auto* array_buffer_sweeper = heap->array_buffer_sweeper();
  if (array_buffer_sweeper->sweeping_in_progress()) {
    auto* tracer = heap->tracer();
    GCTracer::Scope::ScopeId scope_id;

    switch (tracer->GetCurrentCollector()) {
      case GarbageCollector::MINOR_MARK_SWEEPER:
        scope_id = GCTracer::Scope::MINOR_MS_COMPLETE_SWEEP_ARRAY_BUFFERS;
        break;
      case GarbageCollector::SCAVENGER:
        scope_id = GCTracer::Scope::SCAVENGER_COMPLETE_SWEEP_ARRAY_BUFFERS;
        break;
      case GarbageCollector::MARK_COMPACTOR:
        scope_id = GCTracer::Scope::MC_COMPLETE_SWEEP_ARRAY_BUFFERS;
    }

    TRACE_GC_EPOCH_WITH_FLOW(
        tracer, scope_id, ThreadKind::kMain,
        array_buffer_sweeper->GetTraceIdForFlowEvent(scope_id),
        TRACE_EVENT_FLAG_FLOW_IN);
    array_buffer_sweeper->EnsureFinished();
  }
}
void Serializer::Serialize(DirectHandle<HeapObject> obj,int slot_type) {
    DirectHandle<DebugInfo> debug_info;
    CachedTieringDecision cached_tiering_decision;
    bool restore_bytecode = false;
    {
      DisallowGarbageCollection no_gc;
      Tagged<SharedFunctionInfo> sfi = Cast<SharedFunctionInfo>(*obj);
      DCHECK(!sfi->IsApiFunction());
#if V8_ENABLE_WEBASSEMBLY
      // TODO(7110): Enable serializing of Asm modules once the AsmWasmData
      // is context independent.
      DCHECK(!sfi->HasAsmWasmData());
#endif  // V8_ENABLE_WEBASSEMBLY

      if (auto maybe_debug_info = sfi->TryGetDebugInfo(isolate())) {
        debug_info = direct_handle(maybe_debug_info.value(), isolate());
        // Clear debug info.
        if (debug_info->HasInstrumentedBytecodeArray()) {
          restore_bytecode = true;
          sfi->SetActiveBytecodeArray(
              debug_info->OriginalBytecodeArray(isolate()), isolate());
        }
      }
      if (v8_flags.profile_guided_optimization) {
        cached_tiering_decision = sfi->cached_tiering_decision();
        if (cached_tiering_decision > CachedTieringDecision::kEarlySparkplug) {
          sfi->set_cached_tiering_decision(
              CachedTieringDecision::kEarlySparkplug);
        }
      }
    }
    SerializeGeneric(obj, slot_type);
    DisallowGarbageCollection no_gc;
    Tagged<SharedFunctionInfo> sfi = Cast<SharedFunctionInfo>(*obj);
    if (restore_bytecode) {
      sfi->SetActiveBytecodeArray(debug_info->DebugBytecodeArray(isolate()),
                                  isolate());
    }
    if (v8_flags.profile_guided_optimization &&
        cached_tiering_decision > CachedTieringDecision::kEarlySparkplug) {
      sfi->set_cached_tiering_decision(cached_tiering_decision);
    }
    return;
}
int main() {
 unsigned checks=0;
 for(unsigned repeat=0;repeat<10000;++repeat) {
  for(auto collector:{GarbageCollector::SCAVENGER,GarbageCollector::MARK_COMPACTOR,GarbageCollector::MINOR_MARK_SWEEPER}) {
   for(bool pending:{false,true}) {
    Heap heap{{collector}, {pending}};CompleteArrayBufferSweeping(&heap);
    require(!heap.sweep.pending&&heap.sweep.finished==unsigned(pending)&&heap.trace.recorded==unsigned(pending)&&heap.sweep.trace_ids==unsigned(pending));
    if(pending) {
     auto expected=collector==GarbageCollector::SCAVENGER?GCTracer::Scope::SCAVENGER_COMPLETE_SWEEP_ARRAY_BUFFERS:
       collector==GarbageCollector::MARK_COMPACTOR?GCTracer::Scope::MC_COMPLETE_SWEEP_ARRAY_BUFFERS:GCTracer::Scope::MINOR_MS_COMPLETE_SWEEP_ARRAY_BUFFERS;
     require(heap.trace.last==expected);
    }
    CompleteArrayBufferSweeping(&heap);require(heap.sweep.finished==unsigned(pending)&&heap.trace.recorded==unsigned(pending));++checks;
   }
  }
  for(bool enabled:{false,true}) {
   v8_flags.profile_guided_optimization=enabled;
   for(unsigned raw=0;raw<=static_cast<unsigned>(CachedTieringDecision::kNormal);++raw) {
    for(unsigned debug=0;debug<3;++debug) {
     auto sfi=std::make_shared<SharedFunctionInfo>();sfi->decision=static_cast<CachedTieringDecision>(raw);
     if(debug) {sfi->debug=std::make_shared<DebugInfo>(DebugInfo{debug==2});}
     sfi->bytecode=debug==2?23:17;
     Serializer serializer;serializer.Serialize(sfi,7);
     auto expected=enabled&&raw>1?CachedTieringDecision::kEarlySparkplug:static_cast<CachedTieringDecision>(raw);
     require(serializer.calls==1&&serializer.serialized_decision==expected&&serializer.serialized_bytecode==17);
     require(sfi->decision==static_cast<CachedTieringDecision>(raw)&&sfi->bytecode==(debug==2?23:17));
     require(sfi->changes==(debug==2?2u:0u)&&no_gc_depth==0);++checks;
    }
   }
  }
 }
 std::printf("PASS: %u sweep and serializer-state checks\n",checks);
}
