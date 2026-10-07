// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <cstdio>
#include <cstdlib>
#include <sstream>
#include <stdexcept>
#include <string>
enum class FieldSynchronization { kNone, kRelaxed, kAcquireRelease };
struct Instruction { FieldSynchronization synchronization; };
[[noreturn]] void ReportError(const char* text) { throw std::runtime_error(text); }
void require(bool result) { if (!result) { std::abort(); } }
class Generator {
 public:
  std::ostringstream output;
  std::ostream& out() { return output; }
  void Generate(Instruction instruction, const std::string& object,
                const std::string& result_type, const std::string& offset) {
      const char* load;
      switch (instruction.synchronization) {
        case FieldSynchronization::kNone:
          load = "ReadField";
          break;
        case FieldSynchronization::kRelaxed:
          load = "Relaxed_ReadField";
          break;
        case FieldSynchronization::kAcquireRelease:
          ReportError(
              "Torque doesn't support @cppAcquireLoad on untagged data");
      }
      out() << "(" << object << ")->" << load << "<" << result_type << ">("
            << offset << ");\n";

  }
};
int main() {
  size_t checks=0;
  for (unsigned repeat=0; repeat<10000; ++repeat) {
    for (const char* object : {"o", "object_17", "parent->field"}) {
      for (const char* type : {"int32_t", "uint64_t", "Address"}) {
        for (const char* offset : {"0", "4", "(base + index * 8)"}) {
          for (auto mode : {FieldSynchronization::kNone, FieldSynchronization::kRelaxed,
                            FieldSynchronization::kAcquireRelease}) {
            Generator generator;
            if (mode == FieldSynchronization::kAcquireRelease) {
              bool rejected=false;
              try { generator.Generate({mode},object,type,offset); }
              catch (const std::runtime_error& error) {
                require(std::string(error.what())=="Torque doesn't support @cppAcquireLoad on untagged data");
                rejected=true;
              }
              require(rejected && generator.output.str().empty());
            } else {
              generator.Generate({mode},object,type,offset);
              std::string expected="("+std::string(object)+")->"+
                (mode==FieldSynchronization::kNone?"ReadField":"Relaxed_ReadField")+
                "<"+type+">("+offset+");\n";
              require(generator.output.str()==expected);
            }
            ++checks;
          }
        }
      }
    }
  }
  std::printf("PASS: %zu actual C++ load-dispatch branch checks\n",checks);
}
