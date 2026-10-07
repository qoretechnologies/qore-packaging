// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "src/torque/utils.h"
#include <charconv>
#include <cstdio>
#include <cstring>
#include <stdexcept>
#include <system_error>
using v8::internal::torque::Stack;
struct Value {
  static inline int alive = 0;
  static inline int moves_until_throw = -1;
  int number;
  explicit Value(int n) : number(n) { ++alive; }
  Value(const Value&) = delete;
  Value& operator=(const Value&) = delete;
  Value(Value&& other) {
    if (moves_until_throw == 0) { throw std::runtime_error("injected move failure"); }
    if (moves_until_throw > 0) { --moves_until_throw; }
    number = other.number;
    other.number = -1;
    ++alive;
  }
  Value& operator=(Value&& other) noexcept {
    number = other.number;
    other.number = -1;
    return *this;
  }
  ~Value() { --alive; }
};
int main(int argc, char** argv) {
  if (argc == 2) {
    size_t count = 0;
    const char* end = argv[1] + std::strlen(argv[1]);
    const auto parsed = std::from_chars(argv[1], end, count);
    if (parsed.ec != std::errc{} || parsed.ptr != end) { return 2; }
    Stack<int> stack;
    for (int n = 0; n < 4; ++n) { stack.Push(n); }
    auto values = stack.PopMany(count);
    std::printf("%zu values popped\n", values.size());
    return 0;
  }
  if (argc != 1) { return 2; }
  unsigned cases = 0;
  for (unsigned repeat = 0; repeat < 10; ++repeat) {
    for (int size = 0; size <= 32; ++size) {
      for (int count = 0; count <= size; ++count) {
        {
          Stack<Value> stack;
          for (int n = 0; n < size; ++n) { stack.Push(Value(n)); }
          auto values = stack.PopMany(count);
          if (stack.Size() != static_cast<size_t>(size - count)
              || values.size() != static_cast<size_t>(count) || Value::alive != size) { return 1; }
          for (int n = 0; n < count; ++n) {
            if (values[n].number != size - count + n) { return 1; }
          }
          for (int n = size - count; n > 0; --n) {
            if (stack.Pop().number != n - 1) { return 1; }
          }
        }
        if (Value::alive != 0) { return 1; }
        ++cases;
      }
    }
  }
  for (int failed_move = 0; failed_move < 8; ++failed_move) {
    {
      Stack<Value> stack;
      for (int n = 0; n < 8; ++n) { stack.Push(Value(n)); }
      Value::moves_until_throw = failed_move;
      bool caught = false;
      try { stack.PopMany(8); }
      catch (const std::runtime_error&) { caught = true; }
      Value::moves_until_throw = -1;
      if (!caught || stack.Size() != 8 || Value::alive != 8) { return 1; }
      for (int n = 7; n >= 0; --n) {
        const int expected = n < failed_move ? -1 : n;
        if (stack.Pop().number != expected) { return 1; }
      }
    }
    if (Value::alive != 0) { return 1; }
    ++cases;
  }
  std::printf("%u Torque stack cases passed, all values destroyed\n", cases);
  return 0;
}
