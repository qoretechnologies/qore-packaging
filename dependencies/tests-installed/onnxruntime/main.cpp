// Copyright (C) 2026 Qore Technologies, s.r.o.
// SPDX-License-Identifier: MIT
#include <onnxruntime_cxx_api.h>
#include <array>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

int main(int argc, char** argv) {
    try {
        if (argc == 2 && std::string(argv[1]) == "--version-only") {
            std::cout << Ort::GetVersionString() << '\n';
            return 0;
        }
        if (argc != 2) {
            throw std::runtime_error("expected an ONNX model path");
        }
        Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "rpm-sdk-test");
        if (std::string(argv[1]) == "--baseline") {
            std::cout << "ONNX environment initialized without a session or inference\n";
            return 0;
        }
        Ort::SessionOptions options;
        options.SetIntraOpNumThreads(1);
        options.SetInterOpNumThreads(1);
        Ort::Session session(env, argv[1], options);
        auto memory = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
        std::array<float, 3> inputs{-1.0f, 0.0f, 2.0f};
        const std::array<int64_t, 2> shape{3, 1};
        auto tensor = Ort::Value::CreateTensor<float>(memory, inputs.data(), inputs.size(),
                                                       shape.data(), shape.size());
        const char* input_names[] = {"X"};
        const char* output_names[] = {"Y"};
        auto result = session.Run(Ort::RunOptions{nullptr}, input_names, &tensor, 1, output_names, 1);
        if (result.size() != 1 || !result[0].IsTensor()
                || result[0].GetTensorTypeAndShapeInfo().GetShape() != std::vector<int64_t>{3, 1}) {
            throw std::runtime_error("unexpected output shape");
        }
        const auto* output = result[0].GetTensorData<float>();
        const std::array<float, 3> expected{-1.0f, 1.0f, 5.0f};
        for (size_t i = 0; i < expected.size(); ++i) {
            if (!std::isfinite(output[i]) || std::abs(output[i] - expected[i]) > 1e-6f) {
                throw std::runtime_error("incorrect linear model inference");
            }
        }
        bool rejected = false;
        const char* invalid_names[] = {"missing_input"};
        try {
            session.Run(Ort::RunOptions{nullptr}, invalid_names, &tensor, 1, output_names, 1);
        } catch (const Ort::Exception& e) {
            rejected = e.GetOrtErrorCode() == ORT_INVALID_ARGUMENT;
        }
        if (!rejected) {
            throw std::runtime_error("invalid input name was not rejected");
        }
        rejected = false;
        try {
            Ort::Session missing(env, (std::string(argv[1]) + ".missing").c_str(), options);
        } catch (const Ort::Exception& e) {
            rejected = e.GetOrtErrorCode() == ORT_NO_SUCHFILE;
        }
        if (!rejected) {
            throw std::runtime_error("missing model was not rejected");
        }
        std::cout << "ONNX installed SDK: batch inference and two negative cases passed\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
