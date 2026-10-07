// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <cstdio>
#include "src/compiler/raw-machine-assembler.h"
#include "src/compiler/node-properties.h"
#include "src/zone/accounting-allocator.h"
#include "src/zone/zone.h"
namespace i = v8::internal;
namespace c = v8::internal::compiler;
int main() {
    i::AccountingAllocator allocator;
    unsigned checks = 0;
    for (unsigned repeat = 0; repeat < 100; ++repeat) {
        for (unsigned mode = 0; mode < 7; ++mode) {
            i::Zone zone(&allocator, "raw rescheduling regression");
            c::TFGraph graph(&zone);
            i::MachineSignature::Builder signature(&zone, 1, 1);
            signature.AddReturn(i::MachineType::Int32());
            signature.AddParam(i::MachineType::Int32());
            auto* descriptor = c::Linkage::GetSimplifiedCDescriptor(&zone, signature.Get());
            c::RawMachineAssembler assembler(nullptr, &graph, descriptor);
            unsigned expected_returns = 1;
            unsigned expected_throws = 0;
            unsigned expected_terminates = 0;
            if (mode == 0) {
                assembler.Return(assembler.Parameter(0));
            } else if (mode == 1) {
                c::RawMachineLabel positive, negative;
                assembler.Branch(assembler.Parameter(0), &positive, &negative);
                assembler.Bind(&positive);
                assembler.Return(assembler.Int32Constant(1));
                assembler.Bind(&negative);
                assembler.Return(assembler.Int32Constant(2));
                expected_returns = 2;
            } else if (mode == 2) {
                c::RawMachineLabel positive, negative, merge;
                assembler.Branch(assembler.Parameter(0), &positive, &negative);
                assembler.Bind(&positive);
                auto* left = assembler.Int32Constant(10);
                assembler.Goto(&merge);
                assembler.Bind(&negative);
                auto* right = assembler.Int32Constant(20);
                assembler.Goto(&merge);
                assembler.Bind(&merge);
                assembler.Return(assembler.Phi(i::MachineRepresentation::kWord32, left, right));
            } else if (mode == 3) {
                c::RawMachineLabel loop;
                assembler.Goto(&loop);
                assembler.Bind(&loop);
                assembler.Goto(&loop);
                expected_returns = 0;
                expected_terminates = 1;
            } else if (mode == 4) {
                c::RawMachineLabel positive, negative(c::RawMachineLabel::kDeferred);
                assembler.Branch(assembler.Parameter(0), &positive, &negative);
                assembler.Bind(&positive);
                assembler.Return(assembler.Int32Constant(1));
                assembler.Bind(&negative);
                assembler.Unreachable();
                expected_throws = 1;
            } else if (mode == 5) {
                c::RawMachineLabel first, second, fallback;
                int32_t values[] = {1, 2};
                c::RawMachineLabel* labels[] = {&first, &second};
                assembler.Switch(assembler.Parameter(0), &fallback, values, labels, 2);
                assembler.Bind(&first);
                assembler.Return(assembler.Int32Constant(1));
                assembler.Bind(&second);
                assembler.Return(assembler.Int32Constant(2));
                assembler.Bind(&fallback);
                assembler.Return(assembler.Int32Constant(3));
                expected_returns = 3;
            } else {
                c::RawMachineLabel loop, backedge, done;
                assembler.Goto(&loop);
                assembler.Bind(&loop);
                assembler.Branch(assembler.Parameter(0), &backedge, &done);
                assembler.Bind(&backedge);
                assembler.Goto(&loop);
                assembler.Bind(&done);
                assembler.Return(assembler.Int32Constant(4));
                expected_terminates = 1;
            }
            CHECK_EQ(assembler.ExportForOptimization(), &graph);
            CHECK_EQ(graph.end()->InputCount(), expected_returns + expected_throws + expected_terminates);
            unsigned returns = 0, throws = 0, terminates = 0;
            for (int n = 0; n < graph.end()->InputCount(); ++n) {
                switch (graph.end()->InputAt(n)->opcode()) {
                    case c::IrOpcode::kReturn: ++returns; break;
                    case c::IrOpcode::kThrow: ++throws; break;
                    case c::IrOpcode::kTerminate: ++terminates; break;
                    default: UNREACHABLE();
                }
            }
            CHECK_EQ(returns, expected_returns);
            CHECK_EQ(throws, expected_throws);
            CHECK_EQ(terminates, expected_terminates);
            ++checks;
        }
    }
    CHECK_EQ(allocator.GetCurrentMemoryUsage(), 0);
    std::printf("%u actual V8 graph rescheduling controls passed\n", checks);
}
