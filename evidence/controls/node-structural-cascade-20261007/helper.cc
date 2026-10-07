// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "control.h"
const Operation& Block::LastOperation(const Graph& graph) const {return graph.Get(last);}
