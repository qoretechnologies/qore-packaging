# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil
root=Path('work/node-obs-diagnostic-20261006/node-v24.18.1');out=Path('work/node-sweep-serializer-controls-20261007');out.mkdir();extracts=[]
def take(path,start,end):
 s=(root/path).read_text();a=s.index(start);body=s[a:s.index(end,a)].rstrip();extracts.append(dict(file=path,line=s[:a].count('\n')+1,body=body,sha256=hashlib.sha256(body.encode()).hexdigest()));return body
collector=take('deps/v8/src/common/globals.h','enum class GarbageCollector {',';')+';'
cached=take('deps/v8/src/common/globals.h','enum class CachedTieringDecision : int32_t {',';')+';'
sweep=take('deps/v8/src/heap/heap.cc','void CompleteArrayBufferSweeping(Heap* heap)', '\n}  // namespace')
serializer=take('deps/v8/src/snapshot/code-serializer.cc','    DirectHandle<DebugInfo> debug_info;', '\n  } else if (InstanceTypeChecker::IsUncompiledDataWithoutPreparseDataWithJob(')
header=r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
'''+collector+'\n'+cached+r'''
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
'''
# Keep the opaque serializer call in a separate translation unit, matching the
# compiler's inability to infer the full serializer's side effects at this site.
(out/'control.h').write_text(header)
(out/'helper.cc').write_text(r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
void Serializer::SerializeGeneric(DirectHandle<HeapObject> obj,int slot_type) {
 require(slot_type==7);auto* sfi=Cast<SharedFunctionInfo>(*obj);
 serialized_decision=sfi->decision;serialized_bytecode=sfi->bytecode;++calls;
}
''')
source=r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
void require(bool b) {if(!b) {std::abort();}}
Flags v8_flags{};
unsigned no_gc_depth=0;
__attribute__((noinline))
'''+sweep+r'''
void Serializer::Serialize(DirectHandle<HeapObject> obj,int slot_type) {
'''+serializer+r'''
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
'''
(out/'control.cc').write_text(source);(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n');shutil.copy2(root/'deps/v8/LICENSE',out/'V8-LICENSE')
s=Path('work/node-object-dispatch-controls-20261007/run.py').read_text().replace("flags=[]", "flags=['/work/helper.cc']");(out/'run.py').write_text(s)
