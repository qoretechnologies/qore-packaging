Installed ONNX SDK qualification
================================

Copyright 2026 Qore Technologies, s.r.o.

Install the runtime and development RPMs in the target distribution. Copy this
fixture to an empty working directory, then compile and execute it with both
exported discovery mechanisms::

    cmake -S . -B build-debug -DCMAKE_BUILD_TYPE=Debug
    cmake --build build-debug
    build-debug/onnx-consumer /path/to/qore/modules/ml/test/data/test_linear.onnx
    c++ -std=c++17 -g -Wall -Wextra -Werror main.cpp \
      $(pkg-config --cflags --libs libonnxruntime) -o pkgconfig-consumer
    ./pkgconfig-consumer /path/to/qore/modules/ml/test/data/test_linear.onnx

The model comes from the same pinned Qore source as the package qualification.
The consumer checks batched inference across negative, zero and positive inputs,
output dimensions, invalid input-name rejection and missing-model errors.
Run Valgrind on both --baseline and the model invocation. Retain the full reports
and compare against the documented cpuinfo startup-allocation exception; do not
suppress leaks or accept additional inference-related memory errors.
