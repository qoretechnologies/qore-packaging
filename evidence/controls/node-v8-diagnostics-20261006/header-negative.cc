#include "src/compiler/code-assembler.h"
void rejected(v8::internal::compiler::CodeAssembler& a, v8::internal::TNode<v8::internal::Smi> v) { a.BitcastTaggedToWord<int>(v); }
