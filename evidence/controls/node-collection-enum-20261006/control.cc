// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
// Original V8 helper bodies and enums; context loads and runtime calls are recorded.
#include <array>
#include <cstdio>
#include <cstdlib>
void require(bool condition) { if (!condition) { std::abort(); } }
// Distinct sentinel slots model context access; they are not V8 layout offsets.
struct Context { enum Slot { JS_MAP_FUN_INDEX=1, JS_SET_FUN_INDEX=3,
 JS_WEAK_MAP_FUN_INDEX=5, JS_WEAK_SET_FUN_INDEX=7, MAP_SET_INDEX=9,
 SET_ADD_INDEX=11, WEAKMAP_SET_INDEX=13, WEAKSET_ADD_INDEX=15,
 INITIAL_MAP_PROTOTYPE_MAP_INDEX=17, INITIAL_SET_PROTOTYPE_MAP_INDEX=19,
 INITIAL_WEAKMAP_PROTOTYPE_MAP_INDEX=21, INITIAL_WEAKSET_PROTOTYPE_MAP_INDEX=23 };
 int salt;
};
struct JSFunction {};
struct Map {};
struct Object {};
struct JSAny {};
struct Node { const void* context; int slot; };
template<class T> using TNode=Node;
#define CAST(x) (x)
struct BaseCollectionsAssembler {
  enum Variant { kMap, kSet, kWeakMap, kWeakSet };
 unsigned loads=0;
 Node LoadContextElement(Node context,int slot) { ++loads; return {context.context,slot}; }
 __attribute__((noinline)) TNode<JSFunction> GetConstructor(Variant,TNode<Context>);
 __attribute__((noinline)) TNode<JSFunction> GetInitialAddFunction(Variant,TNode<Context>);
 __attribute__((noinline)) TNode<Map> GetInitialCollectionPrototype(Variant,TNode<Context>);
};
namespace Runtime { enum FunctionId { kHasProperty=13, kForInHasProperty=29 }; }
struct CodeStubAssembler {
  enum HasPropertyLookupMode { kHasProperty, kForInHasProperty };
 unsigned calls=0; Runtime::FunctionId called; Node seen_context{},seen_object{},seen_key{};
 Node CallRuntime(Runtime::FunctionId id,Node context,Node object,Node key) {
   ++calls; called=id; seen_context=context; seen_object=object; seen_key=key;
   return {context.context,static_cast<int>(id)};
 }
 __attribute__((noinline)) Node Fallback(HasPropertyLookupMode mode,Node context,Node object,Node key) {
 Node result;
    Runtime::FunctionId fallback_runtime_function_id;
    switch (mode) {
      case kHasProperty:
        fallback_runtime_function_id = Runtime::kHasProperty;
        break;
      case kForInHasProperty:
        fallback_runtime_function_id = Runtime::kForInHasProperty;
        break;
    }

    result =
        CAST(CallRuntime(fallback_runtime_function_id, context, object, key));
 return result;
 }
};
TNode<JSFunction> BaseCollectionsAssembler::GetConstructor(
    Variant variant, TNode<Context> native_context) {
  int index;
  switch (variant) {
    case kMap:
      index = Context::JS_MAP_FUN_INDEX;
      break;
    case kSet:
      index = Context::JS_SET_FUN_INDEX;
      break;
    case kWeakMap:
      index = Context::JS_WEAK_MAP_FUN_INDEX;
      break;
    case kWeakSet:
      index = Context::JS_WEAK_SET_FUN_INDEX;
      break;
  }
  return CAST(LoadContextElement(native_context, index));
}
TNode<JSFunction> BaseCollectionsAssembler::GetInitialAddFunction(
    Variant variant, TNode<Context> native_context) {
  int index;
  switch (variant) {
    case kMap:
      index = Context::MAP_SET_INDEX;
      break;
    case kSet:
      index = Context::SET_ADD_INDEX;
      break;
    case kWeakMap:
      index = Context::WEAKMAP_SET_INDEX;
      break;
    case kWeakSet:
      index = Context::WEAKSET_ADD_INDEX;
      break;
  }
  return CAST(LoadContextElement(native_context, index));
}
TNode<Map> BaseCollectionsAssembler::GetInitialCollectionPrototype(
    Variant variant, TNode<Context> native_context) {
  int initial_prototype_index;
  switch (variant) {
    case kMap:
      initial_prototype_index = Context::INITIAL_MAP_PROTOTYPE_MAP_INDEX;
      break;
    case kSet:
      initial_prototype_index = Context::INITIAL_SET_PROTOTYPE_MAP_INDEX;
      break;
    case kWeakMap:
      initial_prototype_index = Context::INITIAL_WEAKMAP_PROTOTYPE_MAP_INDEX;
      break;
    case kWeakSet:
      initial_prototype_index = Context::INITIAL_WEAKSET_PROTOTYPE_MAP_INDEX;
      break;
  }
  return CAST(LoadContextElement(native_context, initial_prototype_index));
}

int main() {
 using A=BaseCollectionsAssembler; using C=CodeStubAssembler;
 const std::array<A::Variant,4> modes{A::kMap,A::kSet,A::kWeakMap,A::kWeakSet};
 const std::array<std::array<int,4>,3> expected{{{1,3,5,7},{9,11,13,15},{17,19,21,23}}};
 std::array<Context,4> contexts{{{0},{1},{-1},{999}}}; unsigned checks=0;
 for(unsigned repeat=0;repeat<10000;++repeat) {
  for(auto& context:contexts) {
   Node context_node{&context,0};
   for(unsigned i=0;i<modes.size();++i) {
    A assembler;
    const std::array<Node,3> results{assembler.GetConstructor(modes[i],context_node),
      assembler.GetInitialAddFunction(modes[i],context_node),assembler.GetInitialCollectionPrototype(modes[i],context_node)};
    require(assembler.loads==3);
    for(unsigned j=0;j<results.size();++j) { require(results[j].context==&context && results[j].slot==expected[j][i]); ++checks; }
   }
   for(auto mode:{C::kHasProperty,C::kForInHasProperty}) {
    C assembler; Node object{&context,73},key{&context,-19};
    Node result=assembler.Fallback(mode,context_node,object,key);
    int expected_id=mode==C::kHasProperty?13:29;
    require(assembler.calls==1 && static_cast<int>(assembler.called)==expected_id
      && result.context==&context && result.slot==expected_id
      && assembler.seen_context.context==&context && assembler.seen_context.slot==0
      && assembler.seen_object.context==&context && assembler.seen_object.slot==73
      && assembler.seen_key.context==&context && assembler.seen_key.slot==-19);
    ++checks;
   }
  }
 }
 std::printf("PASS: %u collection and property dispatch checks across every declared mode\n",checks);
}
