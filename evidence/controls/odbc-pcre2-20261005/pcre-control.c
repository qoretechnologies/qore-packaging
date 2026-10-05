/* Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT */
#define PCRE2_CODE_UNIT_WIDTH 8
#include <pcre2.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc, char** argv) {
    int error;
    PCRE2_SIZE offset;
    const char* pattern = "\\.qm$";
    const char* text = "/fixture/module-odbc/test/array-binding.qtest";
    const size_t length = strlen(text);
    pcre2_code* code = pcre2_compile((PCRE2_SPTR)pattern, PCRE2_ZERO_TERMINATED, PCRE2_UTF, &error, &offset, NULL);
    if (!code || pcre2_jit_compile(code, PCRE2_JIT_COMPLETE)) { return 1; }
    pcre2_match_data* data = pcre2_match_data_create_from_pattern(code, NULL);
    if (!data) { pcre2_code_free(code); return 2; }
    for (int shift = 0; shift < 16; ++shift) {
        char* buffer = malloc(128);
        if (!buffer) { return 3; }
        for (int padding = 0; padding < 256; ++padding) {
            if (argc > 1 && strcmp(argv[1], "defined") == 0) { memset(buffer, padding, 128); }
            memcpy(buffer + shift, text, length + 1);
            int rc = pcre2_match(code, (PCRE2_SPTR)(buffer + shift), length, 0, 0, data, NULL);
            if (rc != PCRE2_ERROR_NOMATCH) { return 4; }
            // The same pattern must find a real suffix independently of padding.
            memcpy(buffer + shift + length - 3, ".qm", 3);
            rc = pcre2_match(code, (PCRE2_SPTR)(buffer + shift), length, 0, 0, data, NULL);
            if (rc != 1) { return 5; }
        }
        free(buffer);
    }
    pcre2_match_data_free(data);
    pcre2_code_free(code);
    puts("8192 JIT suffix checks passed across 16 alignments and 256 padding values");
    return 0;
}
