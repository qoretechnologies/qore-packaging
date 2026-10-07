// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
using namespace interpreter;
BytecodeArrayIterator::BytecodeArrayIterator(BytecodeArray* array,int offset):array_(array),offset_(offset) {require(IsValidOffset(array,offset));}
bool BytecodeArrayIterator::IsValidOffset(BytecodeArray* array,int offset) {return offset>=0 && static_cast<size_t>(offset)<array->values.size();}
bool BytecodeArrayIterator::done() const {return static_cast<size_t>(offset_)>=array_->values.size();}
void BytecodeArrayIterator::Advance() {require(!done());++offset_;}
void BytecodeArrayIterator::SetOffset(int offset) {require(IsValidOffset(array_,offset));offset_=offset;}
int BytecodeArrayIterator::current_offset() const {require(!done());return offset_;}
Bytecode BytecodeArrayIterator::current_bytecode() const {require(!done());return array_->values[offset_].opcode;}
int BytecodeArrayIterator::GetJumpTargetOffset() const {require(current_bytecode()==Bytecode::kJumpLoop);return array_->values[offset_].target;}
int BytecodeArrayIterator::GetImmediateOperand(int operand) const {require(operand==1 && current_bytecode()==Bytecode::kJumpLoop);return array_->values[offset_].level;}
int BytecodeArrayIterator::GetSlotOperand(int operand) const {require(operand==2 && current_bytecode()==Bytecode::kJumpLoop);return array_->values[offset_].slot;}
