// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#pragma once
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <optional>
void require(bool);
#define DCHECK(a) require(a)
#define V8_ENABLE_WEBASSEMBLY 1
enum class GarbageCollector { SCAVENGER, MARK_COMPACTOR, MINOR_MARK_SWEEPER };
enum class CachedTieringDecision : int32_t {
  kPending,
  kEarlySparkplug,
  kDelayMaglev,
  kEarlyMaglev,
  kEarlyTurbofan,
  kNormal,
};
struct GCTracer {
 struct Scope {enum ScopeId {MINOR_MS_COMPLETE_SWEEP_ARRAY_BUFFERS,SCAVENGER_COMPLETE_SWEEP_ARRAY_BUFFERS,MC_COMPLETE_SWEEP_ARRAY_BUFFERS};};
 GarbageCollector collector;
 unsigned recorded=0;Scope::ScopeId last=Scope::MC_COMPLETE_SWEEP_ARRAY_BUFFERS;
 GarbageCollector GetCurrentCollector() const {return collector;}
};
struct Sweeper {
 bool pending;
 unsigned finished=0;unsigned trace_ids=0;
 bool sweeping_in_progress() const {return pending;}
 unsigned GetTraceIdForFlowEvent(GCTracer::Scope::ScopeId scope) {++trace_ids;return 100+static_cast<unsigned>(scope);}
 void EnsureFinished() {require(pending);pending=false;++finished;}
};
struct Heap {
 GCTracer trace;Sweeper sweep;
 Sweeper* array_buffer_sweeper() {return &sweep;}
 GCTracer* tracer() {return &trace;}
};
enum class ThreadKind {kMain};
constexpr unsigned TRACE_EVENT_FLAG_FLOW_IN=1;
inline void record_trace(GCTracer* tracer,GCTracer::Scope::ScopeId scope,ThreadKind kind,unsigned id,unsigned flags) {
 require(kind==ThreadKind::kMain&&id==100+static_cast<unsigned>(scope)&&flags==1);
 ++tracer->recorded;tracer->last=scope;
}
#define TRACE_GC_EPOCH_WITH_FLOW(tracer,scope,kind,id,flags) record_trace(tracer,scope,kind,id,flags)
struct Flags {bool profile_guided_optimization;};
extern Flags v8_flags;
struct HeapObject {virtual ~HeapObject()=default;};
struct DebugInfo {
 bool instrumented;
 bool HasInstrumentedBytecodeArray() const {return instrumented;}
 int OriginalBytecodeArray(int) const {return 17;}
 int DebugBytecodeArray(int) const {return 23;}
};
struct SharedFunctionInfo:HeapObject {
 CachedTieringDecision decision=CachedTieringDecision::kPending;
 std::shared_ptr<DebugInfo> debug;
 int bytecode=17;
 unsigned changes=0;
 bool IsApiFunction() const {return false;}
 bool HasAsmWasmData() const {return false;}
 std::optional<std::shared_ptr<DebugInfo>> TryGetDebugInfo(int) {if(debug) {return debug;}return std::nullopt;}
 void SetActiveBytecodeArray(int value,int) {bytecode=value;++changes;}
 CachedTieringDecision cached_tiering_decision() const {return decision;}
 void set_cached_tiering_decision(CachedTieringDecision value) {decision=value;}
};
template<class T> using DirectHandle=std::shared_ptr<T>;
template<class T> using Tagged=T*;
template<class T> T* Cast(HeapObject& value) {auto* result=dynamic_cast<T*>(&value);require(result);return result;}
template<class T> DirectHandle<T> direct_handle(const std::shared_ptr<T>& p,int) {return p;}
extern unsigned no_gc_depth;
struct DisallowGarbageCollection {
 DisallowGarbageCollection() {++no_gc_depth;}
 ~DisallowGarbageCollection() {--no_gc_depth;}
};
struct Serializer {
 CachedTieringDecision serialized_decision=CachedTieringDecision::kPending;
 int serialized_bytecode=-1;
 unsigned calls=0;
 int isolate() const {return 0;}
 void SerializeGeneric(DirectHandle<HeapObject> obj,int slot_type);
 void Serialize(DirectHandle<HeapObject> obj,int slot_type);
};
