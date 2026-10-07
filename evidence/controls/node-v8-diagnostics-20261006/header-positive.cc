#include "src/compiler/code-assembler.h"
void allowed(v8::internal::compiler::CodeAssembler& a, v8::internal::TNode<v8::internal::Smi> v) { a.BitcastTaggedToWordForTagAndSmiBits(v); }
