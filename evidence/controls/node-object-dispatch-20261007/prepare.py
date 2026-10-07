# Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
from pathlib import Path
import hashlib,json,shutil,subprocess
root=Path('work/node-obs-diagnostic-20261006/node-v24.18.1');out=Path('work/node-object-dispatch-controls-20261007');out.mkdir();extracts=[]
def take(path,start,end,after=None):
 s=(root/path).read_text();a=s.index(start,s.index(after) if after else 0);b=s.index(end,a);body=s[a:b].rstrip();extracts.append(dict(file=path,line=s[:a].count('\n')+1,body=body,sha256=hashlib.sha256(body.encode()).hexdigest()));return body
wasm_enum=take('deps/v8/src/compiler/wasm-compiler-definitions.h','enum WasmCallKind {',';')+';'
kind_enum=take('deps/v8/src/compiler/linkage.h','  enum Kind {',';')+';'
wasm_body=take('deps/v8/src/compiler/wasm-compiler-definitions.cc','  CallDescriptor::Kind descriptor_kind;','\n  CallDescriptor::Flags flags')
property_enum=take('deps/v8/src/ast/ast.h','  enum Kind : uint8_t { METHOD',';')+';'
value_enum=take('deps/v8/src/objects/literal-objects.h','  enum ValueKind {',';')+';'
literal_body=take('deps/v8/src/objects/literal-objects.cc','    ClassBoilerplate::ValueKind value_kind;','\n    ObjectDescriptor<IsolateT>& desc')
clone_enum=take('deps/v8/src/maglev/maglev-ir.h','  enum Type : uint8_t {',';',after='class VirtualObject :')+';'
clone=take('deps/v8/src/maglev/maglev-ir.h','  VirtualObject* Clone(uint32_t','\n  uint32_t slot_count()',after='class VirtualObject :')
source=r'''// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Unchanged dispatch/clone bodies with typed descriptor and arena adapters.
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <memory>
#include <stdexcept>
#include <vector>
#include <utility>
#define V8_ENABLE_WEBASSEMBLY 1
void require(bool ok) { if(!ok) { std::abort(); } }
#define DCHECK_IMPLIES(a,b) require(!(a)||(b))
struct Unreachable {};
[[noreturn]] void unreachable() { throw Unreachable{}; }
#define UNREACHABLE() unreachable()
'''+wasm_enum+'\nstruct CallDescriptor {\n'+kind_enum+r'''
};
struct Signature { uint64_t hash; };
constexpr uint64_t kInvalidWasmSignatureHash = UINT64_MAX;
namespace wasm { struct SignatureHasher { static uint64_t Hash(const Signature* sig) { return sig->hash; } }; }
__attribute__((noinline)) std::pair<CallDescriptor::Kind,uint64_t> Descriptor(WasmCallKind call_kind, const Signature* fsig) {
'''+wasm_body+r'''
return {descriptor_kind,signature_hash};
}
struct ClassLiteral { struct Property {
'''+property_enum+r'''
 Kind kind_;bool computed,private_;
 Kind kind() const { return kind_; }
 bool is_computed_name() const { return computed; }
 bool is_private() const { return private_; }
}; };
struct ClassBoilerplate {
'''+value_enum+r'''
};
struct Emission { ClassBoilerplate::ValueKind kind;int index; };
__attribute__((noinline)) std::pair<std::vector<Emission>,int> Literal(const std::vector<ClassLiteral::Property>& props, int dynamic_argument_index) {
 std::vector<Emission> result;
 for(const auto& entry:props) { const auto* property=&entry;
'''+literal_body+r'''
 result.push_back({value_kind,value_index});
 dynamic_argument_index+=property->is_computed_name()?2:1;
 }
 return {std::move(result),dynamic_argument_index};
}
struct ValueNode { unsigned value; };
struct InlinedAllocation { unsigned identity; };
struct VirtualObject;
struct Zone {
 std::vector<std::unique_ptr<ValueNode*[]>> arrays;
 std::vector<std::unique_ptr<VirtualObject>> objects;
 int allowance=-1;
 void allocate() { if(allowance==0) { throw std::bad_alloc(); } if(allowance>0) {--allowance;} }
 template<class T> T* AllocateArray(uint32_t n) {
  static_assert(std::is_same_v<T,ValueNode*>);allocate();
  auto array=std::make_unique<T[]>(n);auto* ptr=array.get();arrays.push_back(std::move(array));return ptr;
 }
};
struct NodeBase {
 template<class T,class... Args> static T* New(Zone* zone, int, Args&&... args) {
  zone->allocate();auto value=std::make_unique<T>(std::forward<Args>(args)...);auto* ptr=value.get();zone->objects.push_back(std::move(value));return ptr;
 }
};
struct VirtualObject {
'''+clone_enum+r'''
 Type type_=kDefault;int map_;uint32_t id,count;ValueNode** slots;InlinedAllocation* allocation_=nullptr;
 VirtualObject(int map,uint32_t object_id,uint32_t n,ValueNode** data):map_(map),id(object_id),count(n),slots(data) {}
 int map() const { return map_; }
 uint32_t slot_count() const { return count; }
 ValueNode* get_by_index(uint32_t n) const { require(n<count);return slots[n]; }
 void set_by_index(uint32_t n,ValueNode* value) { require(n<count);slots[n]=value; }
 InlinedAllocation* allocation() const { return allocation_; }
 void set_allocation(InlinedAllocation* value) { allocation_=value; }
 __attribute__((noinline))
'''+clone+r'''
};
'''
(out/'control-prefix.cc').write_text(source)
(out/'source-extracts.json').write_text(json.dumps(extracts,indent=2)+'\n');shutil.copy2(root/'deps/v8/LICENSE',out/'V8-LICENSE')
