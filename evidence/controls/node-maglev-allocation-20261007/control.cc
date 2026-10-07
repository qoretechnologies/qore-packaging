// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
Flags v8_flags{};
InlinedAllocation* MaglevGraphBuilder::BuildInlinedAllocation(
    VirtualObject* vobject, AllocationType allocation_type) {
  current_interpreter_frame_.add_object(vobject);
  InlinedAllocation* allocation;
  switch (vobject->type()) {
    case VirtualObject::kHeapNumber:
      allocation =
          BuildInlinedAllocationForHeapNumber(vobject, allocation_type);
      break;
    case VirtualObject::kFixedDoubleArray:
      allocation =
          BuildInlinedAllocationForDoubleFixedArray(vobject, allocation_type);
      break;
    case VirtualObject::kConsString:
      allocation =
          BuildInlinedAllocationForConsString(vobject, allocation_type);
      break;
    case VirtualObject::kDefault: {
      SmallZoneVector<ValueNode*, 8> values(zone());
      vobject->ForEachInput([&](ValueNode*& node) {
        ValueNode* value_to_push;
        if (node->Is<VirtualObject>()) {
          VirtualObject* nested = node->Cast<VirtualObject>();
          node = BuildInlinedAllocation(nested, allocation_type);
          value_to_push = node;
        } else if (node->Is<Float64Constant>()) {
          value_to_push = BuildInlinedAllocationForHeapNumber(
              CreateHeapNumber(node->Cast<Float64Constant>()->value()),
              allocation_type);
        } else {
          value_to_push = GetTaggedValue(node);
        }
        values.push_back(value_to_push);
      });
      allocation =
          ExtendOrReallocateCurrentAllocationBlock(allocation_type, vobject);
      AddNonEscapingUses(allocation, static_cast<int>(values.size()));
      if (vobject->has_static_map()) {
        AddNonEscapingUses(allocation, 1);
        BuildStoreMap(allocation, vobject->map(),
                      StoreMap::Kind::kInlinedAllocation);
      }
      for (uint32_t i = 0; i < values.size(); i++) {
        BuildInitializeStore(allocation, values[i], (i + 1) * kTaggedSize);
      }
      if (is_loop_effect_tracking()) {
        loop_effects_->allocations.insert(allocation);
      }
      break;
    }
  }
  if (v8_flags.maglev_allocation_folding < 2) {
    ClearCurrentAllocationBlock();
  }
  return allocation;
}

struct Expected {
  VirtualObject* node;
  std::vector<ValueNode*> inputs;
};
void verify(MaglevGraphBuilder& builder,InlinedAllocation* result,const Expected& e,AllocationType generation) {
  require(result->type==e.node->type() && result->generation==generation);
  if (e.node->type()!=VirtualObject::kDefault) { return; }
  require(result->stores.size()==e.inputs.size());
  require(result->uses==e.inputs.size()+unsigned(e.node->has_static_map()));
  require(result->map==(e.node->has_static_map()?e.node->map():-1));
  require(builder.effects.allocations.contains(result)==builder.loop);
  for (unsigned i=0;i<e.inputs.size();++i) {
    auto* original=e.inputs[i]; auto* stored=result->stores[i].second;
    require(result->stores[i].first==static_cast<int>((i+1)*kTaggedSize));
    if (original->Is<VirtualObject>()) {
      require(stored->Is<InlinedAllocation>() && e.node->inputs[i]==stored);
      auto* nested=original->Cast<VirtualObject>();
      verify(builder,stored->Cast<InlinedAllocation>(),Expected{nested,{}},generation);
    } else if (original->Is<Float64Constant>()) {
      require(e.node->inputs[i]==original && stored->Is<InlinedAllocation>());
      require(stored->Cast<InlinedAllocation>()->number==original->Cast<Float64Constant>()->value());
    } else { require(stored==original && e.node->inputs[i]==original); }
  }
}
int main() {
  unsigned checks=0,failures=0;
  for (unsigned repeat=0;repeat<30;++repeat) {
    for (auto type:{VirtualObject::kDefault,VirtualObject::kHeapNumber,VirtualObject::kFixedDoubleArray,VirtualObject::kConsString}) {
      for (unsigned fields:{0u,1u,8u,12u}) {for (unsigned mode=0;mode<12;++mode) {
        for (auto generation:{AllocationType::kYoung,AllocationType::kOld}) {
          for (int fail=-1;fail<12;++fail) {
            {
              MaglevGraphBuilder b;b.loop=mode&1;v8_flags.maglev_allocation_folding=mode/4;
              auto* v=b.make<VirtualObject>(type,bool(mode&2),171);
              for (unsigned i=0;i<fields;++i) {
                if (i%3==0) {v->inputs.push_back(b.make<VirtualObject>(static_cast<VirtualObject::Type>((i/3)%4),true,172));}
                else if (i%3==1) {v->inputs.push_back(b.make<Float64Constant>(i+0.25));}
                else {v->inputs.push_back(b.make<TaggedValue>(i));}
              }
              Expected expected{v,v->inputs};b.calls=0;b.fail_at=fail;
              try {
                auto* allocation=b.BuildInlinedAllocation(v,generation);
                verify(b,allocation,expected,generation);
                require(b.clears==(v8_flags.maglev_allocation_folding<2?b.current_interpreter_frame_.objects.size():0));
                require(fail<0 || static_cast<unsigned>(fail)>=b.calls);
              } catch (const std::bad_alloc&) {
                require(fail>=0 && b.calls==static_cast<unsigned>(fail+1));++failures;
              }
            }
            require(ValueNode::live==0);++checks;
          }
        }
      }}
    }
  }
  std::printf("PASS: %u typed allocation-dispatch cases, including %u injected failures\n",checks,failures);
}
