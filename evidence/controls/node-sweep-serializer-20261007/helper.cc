// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
void Serializer::SerializeGeneric(DirectHandle<HeapObject> obj,int slot_type) {
 require(slot_type==7);auto* sfi=Cast<SharedFunctionInfo>(*obj);
 serialized_decision=sfi->decision;serialized_bytecode=sfi->bytecode;++calls;
}
