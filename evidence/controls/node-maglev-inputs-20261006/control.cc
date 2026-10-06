// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <array>
#include <cstdio>
#include <cstdlib>
#include <initializer_list>
#include "src/base/hashing.h"
struct ValueNode { unsigned index; };
static std::array<ValueNode,128> values;
__attribute__((noinline)) ValueNode* convert(ValueNode* value,unsigned representation) {
 return representation ? &values[(value->index+representation)%values.size()] : value;
}
__attribute__((noinline)) size_t node_hash(std::initializer_list<ValueNode*> raw_inputs,unsigned representation) {
 std::array<ValueNode*,1> inputs;
 int i=0;
 for (ValueNode* raw_input:raw_inputs) { inputs[i]=convert(raw_input,representation);++i; }
 size_t result=0;
 for (const auto& inp:inputs) { result=v8::base::hash_value(inp); }
 return result;
}
int main() {
 unsigned checks=0;
 for(unsigned i=0;i<values.size();++i) { values[i].index=i; }
 for(unsigned n=0;n<1000;++n) {
  for(unsigned i=0;i<values.size();++i) {
   for(unsigned repr=0;repr<6;++repr) {
    auto* expected=&values[(i+repr)%values.size()];
    if(node_hash({&values[i]},repr)!=v8::base::hash_value(expected)) { return 1; }
    ++checks;
   }
  }
 }
 std::printf("%u fixed-arity conversion/hash checks passed\n",checks);
}
