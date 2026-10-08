# Copyright 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
from pyarrow.lib cimport Array
cimport pyarrow.includes

def length(Array value):
    return len(value)
