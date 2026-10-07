// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
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
enum WasmCallKind {
  kWasmFunction,
  kWasmIndirectFunction,
  kWasmImportWrapper,
  kWasmCapiFunction
};
struct CallDescriptor {
  enum Kind {
    kCallCodeObject,         // target is a Code object
    kCallJSFunction,         // target is a JSFunction object
    kCallAddress,            // target is a machine pointer
#if V8_ENABLE_WEBASSEMBLY    // ↓ WebAssembly only
    kCallWasmCapiFunction,   // target is a Wasm C API function
    kCallWasmFunction,       // target is a wasm function
    kCallWasmFunctionIndirect,  // target is a wasm function that will be called
                                // indirectly
    kCallWasmImportWrapper,     // target is a wasm import wrapper
#endif                       // ↑ WebAssembly only
    kCallBuiltinPointer,     // target is a builtin pointer
  };
};
struct Signature { uint64_t hash; };
constexpr uint64_t kInvalidWasmSignatureHash = UINT64_MAX;
namespace wasm { struct SignatureHasher { static uint64_t Hash(const Signature* sig) { return sig->hash; } }; }
__attribute__((noinline)) std::pair<CallDescriptor::Kind,uint64_t> Descriptor(WasmCallKind call_kind, const Signature* fsig) {
  CallDescriptor::Kind descriptor_kind;
  uint64_t signature_hash = kInvalidWasmSignatureHash;

  switch (call_kind) {
    case kWasmFunction:
      descriptor_kind = CallDescriptor::kCallWasmFunction;
      break;
    case kWasmIndirectFunction:
      descriptor_kind = CallDescriptor::kCallWasmFunctionIndirect;
      signature_hash = wasm::SignatureHasher::Hash(fsig);
      break;
    case kWasmImportWrapper:
      descriptor_kind = CallDescriptor::kCallWasmImportWrapper;
      break;
    case kWasmCapiFunction:
      descriptor_kind = CallDescriptor::kCallWasmCapiFunction;
      break;
  }
return {descriptor_kind,signature_hash};
}
struct ClassLiteral { struct Property {
  enum Kind : uint8_t { METHOD, GETTER, SETTER, FIELD, AUTO_ACCESSOR };
 Kind kind_;bool computed,private_;
 Kind kind() const { return kind_; }
 bool is_computed_name() const { return computed; }
 bool is_private() const { return private_; }
}; };
struct ClassBoilerplate {
  enum ValueKind { kData, kGetter, kSetter, kAutoAccessor };
};
struct Emission { ClassBoilerplate::ValueKind kind;int index; };
__attribute__((noinline)) std::pair<std::vector<Emission>,int> Literal(const std::vector<ClassLiteral::Property>& props, int dynamic_argument_index) {
 std::vector<Emission> result;
 for(const auto& entry:props) { const auto* property=&entry;
    ClassBoilerplate::ValueKind value_kind;
    int value_index = dynamic_argument_index;
    switch (property->kind()) {
      case ClassLiteral::Property::METHOD:
        value_kind = ClassBoilerplate::kData;
        break;
      case ClassLiteral::Property::GETTER:
        value_kind = ClassBoilerplate::kGetter;
        break;
      case ClassLiteral::Property::SETTER:
        value_kind = ClassBoilerplate::kSetter;
        break;
      case ClassLiteral::Property::FIELD:
        DCHECK_IMPLIES(property->is_computed_name(), !property->is_private());
        if (property->is_computed_name()) {
          ++dynamic_argument_index;
        }
        continue;
      case ClassLiteral::Property::AUTO_ACCESSOR:
        value_kind = ClassBoilerplate::kAutoAccessor;
        // Auto-accessors have two arguments (getter and setter).
        ++dynamic_argument_index;
    }
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
  enum Type : uint8_t {
    kDefault,
    kHeapNumber,
    kFixedDoubleArray,
    kConsString,

    kLast = kConsString
  };
 Type type_=kDefault;int map_;uint32_t id,count;ValueNode** slots;InlinedAllocation* allocation_=nullptr;
 VirtualObject(int map,uint32_t object_id,uint32_t n,ValueNode** data):map_(map),id(object_id),count(n),slots(data) {}
 int map() const { return map_; }
 uint32_t slot_count() const { return count; }
 ValueNode* get_by_index(uint32_t n) const { require(n<count);return slots[n]; }
 void set_by_index(uint32_t n,ValueNode* value) { require(n<count);slots[n]=value; }
 InlinedAllocation* allocation() const { return allocation_; }
 void set_allocation(InlinedAllocation* value) { allocation_=value; }
 __attribute__((noinline))
  VirtualObject* Clone(uint32_t new_object_id, Zone* zone,
                       bool empty_clone = false) const {
    VirtualObject* result;
    switch (type_) {
      case kHeapNumber:
      case kFixedDoubleArray:
      case kConsString:
        UNREACHABLE();
      case kDefault: {
        ValueNode** slots = zone->AllocateArray<ValueNode*>(slot_count());
        result = NodeBase::New<VirtualObject>(zone, 0, map(), new_object_id,
                                              slot_count(), slots);
        break;
      }
    }
    if (empty_clone) return result;

    // Copy content
    switch (type_) {
      case kHeapNumber:
      case kFixedDoubleArray:
      case kConsString:
        UNREACHABLE();
      case kDefault: {
        for (uint32_t i = 0; i < slot_count(); i++) {
          result->set_by_index(i, get_by_index(i));
        }
        break;
      }
    }
    result->set_allocation(allocation());
    return result;
  }
};
int main() {
 unsigned checks=0;
 const std::array calls{kWasmFunction,kWasmIndirectFunction,kWasmImportWrapper,kWasmCapiFunction};
 const std::array kinds{CallDescriptor::kCallWasmFunction,CallDescriptor::kCallWasmFunctionIndirect,CallDescriptor::kCallWasmImportWrapper,CallDescriptor::kCallWasmCapiFunction};
 for(unsigned repeat=0;repeat<10000;++repeat) {
  Signature sig{uint64_t(repeat)*65537};
  for(unsigned i=0;i<calls.size();++i) {
   auto [kind,hash]=Descriptor(calls[i],&sig);require(kind==kinds[i]);require(hash==(i==1?sig.hash:kInvalidWasmSignatureHash));++checks;
  }
  using P=ClassLiteral::Property;using B=ClassBoilerplate;
  const std::array props{P::METHOD,P::GETTER,P::SETTER,P::FIELD,P::AUTO_ACCESSOR};
  for(bool computed:{false,true}) {for(bool private_:{false,true}) {
   if(computed&&private_) { continue; }
   std::vector<P> values;
   for(auto mode:props) { values.push_back({mode,computed,private_}); }
   for(int offset:{0,1,123}) {
    auto [emitted,end]=Literal(values,offset);require(emitted.size()==4);
    const std::array expected{B::kData,B::kGetter,B::kSetter,B::kAutoAccessor};
    int index=offset;
    for(unsigned i=0;i<4;++i) {
     if(i==3&&computed) { ++index; }
     require(emitted[i].kind==expected[i]);require(emitted[i].index==index);
     index+=(computed?2:1)+(i==3?1:0);
    }
    require(end==index);++checks;
   }
  }}
 }
 for(unsigned repeat=0;repeat<500;++repeat) {
  for(uint32_t n:{0u,1u,32u,1024u}) {
   std::vector<ValueNode> values(n);std::vector<ValueNode*> slots(n);
   for(uint32_t i=0;i<n;++i) {values[i].value=i;slots[i]=i%3?&values[i]:nullptr;}
   InlinedAllocation allocation{repeat};VirtualObject original(42,repeat,n,slots.data());original.set_allocation(&allocation);
   for(bool empty:{false,true}) {
    Zone zone;auto* copy=original.Clone(repeat+1,&zone,empty);
    require(copy!=&original);require(copy->map()==42);require(copy->id==repeat+1);require(copy->slot_count()==n);
    require(zone.arrays.size()==1&&zone.objects.size()==1);
    if(empty) {require(copy->allocation()==nullptr);} else {
     require(copy->allocation()==&allocation);
     for(uint32_t i=0;i<n;++i) {require(copy->get_by_index(i)==slots[i]);}
    }
    if(n) {copy->set_by_index(0,&values[0]);require(original.get_by_index(0)==nullptr);}
    ++checks;
   }
   for(auto kind:{VirtualObject::kHeapNumber,VirtualObject::kFixedDoubleArray,VirtualObject::kConsString}) {
    original.type_=kind;Zone zone;bool rejected=false;
    try { original.Clone(2,&zone); } catch(const Unreachable&) {rejected=true;}
    require(rejected);require(zone.arrays.empty()&&zone.objects.empty());++checks;
   }
   original.type_=VirtualObject::kDefault;
   for(int allowance:{0,1}) {
    Zone zone;zone.allowance=allowance;bool failed=false;
    try {original.Clone(2,&zone);} catch(const std::bad_alloc&) {failed=true;}
    require(failed);require(zone.objects.empty());require(zone.arrays.size()==static_cast<size_t>(allowance));++checks;
   }
  }
 }
 std::printf("PASS: %u descriptor, literal-mode, clone ownership and allocation-failure checks\n",checks);
}
