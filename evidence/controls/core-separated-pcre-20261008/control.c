/* Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT */
#define PCRE2_CODE_UNIT_WIDTH 8
#include <pcre2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char** argv) {
    if (argc != 2 || (strcmp(argv[1], "defined") && strcmp(argv[1], "undefined"))) { return 2; }
    int error;
    PCRE2_SIZE offset;
    const char* pattern = ".+\\.(qc|ql)$";
    const char* subjects[] = {"resource.txt", "resource.qc", "resource.ql", ".qc", "a.qc.txt",
        "long-module-resource-0123456789.qc", "resource.QC", "x.qc\n", "x.ql\nrest", ""};
    const int expected[] = {-1, 2, 2, -1, -1, 2, -1, 2, -1, -1};
    const int defined = !strcmp(argv[1], "defined");
    pcre2_code* code = pcre2_compile((PCRE2_SPTR)pattern, PCRE2_ZERO_TERMINATED, PCRE2_UTF,
        &error, &offset, NULL);
    if (!code) { return 3; }
    if (pcre2_jit_compile(code, PCRE2_JIT_COMPLETE)) { pcre2_code_free(code); return 4; }
    pcre2_match_data* jit = pcre2_match_data_create_from_pattern(code, NULL);
    pcre2_match_data* ref = pcre2_match_data_create_from_pattern(code, NULL);
    int rc = 0;
    size_t checks = 0;
    if (!jit || !ref) { rc = 5; goto cleanup; }
    for (size_t item = 0; item < sizeof(subjects) / sizeof(*subjects); ++item) {
        size_t len = strlen(subjects[item]);
        for (int shift = 0; shift < 16; ++shift) {
            char* buffer = malloc(128);
            if (!buffer) { rc = 6; goto cleanup; }
            for (int padding = 0; padding < 256; ++padding) {
                if (defined) { memset(buffer, padding, 128); }
                memcpy(buffer + shift, subjects[item], len + 1);
                int result = pcre2_match(code, (PCRE2_SPTR)(buffer + shift), len, 0, 0, jit, NULL);
                int oracle = pcre2_match(code, (PCRE2_SPTR)(buffer + shift), len, 0, PCRE2_NO_JIT, ref, NULL);
                if (result != oracle || result != expected[item]) { free(buffer); rc = 7; goto cleanup; }
                ++checks;
                if (result > 0) {
                    PCRE2_SIZE* a = pcre2_get_ovector_pointer(jit);
                    PCRE2_SIZE* b = pcre2_get_ovector_pointer(ref);
                    if (memcmp(a, b, 2 * (size_t)result * sizeof(*a))) { free(buffer); rc = 8; goto cleanup; }
                    ++checks;
                }
            }
            free(buffer);
        }
    }
cleanup:
    pcre2_match_data_free(jit);
    pcre2_match_data_free(ref);
    pcre2_code_free(code);
    if (!rc) { printf("PASS: %zu result/capture checks; padding=%s\n", checks, argv[1]); }
    return rc;
}
