# Copyright (C) 2026 Qore Technologies, s.r.o.
# SPDX-License-Identifier: MIT
cmake_minimum_required(VERSION 3.21...3.31)
project(OnnxInstalledSdk LANGUAGES CXX)
find_package(onnxruntime 1.22 CONFIG REQUIRED)
add_executable(onnx-consumer main.cpp)
target_compile_features(onnx-consumer PRIVATE cxx_std_17)
target_compile_options(onnx-consumer PRIVATE -Wall -Wextra -Werror)
target_link_libraries(onnx-consumer PRIVATE onnxruntime::onnxruntime)
