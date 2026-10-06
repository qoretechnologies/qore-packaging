/* Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT */
#include <assert.h>
#include <stdio.h>
#include <proj.h>
int main(void) {
    const char *source[] = {"EPSG:99999", "+proj=not-a-real-projection", "", "EPSG:4326"};
    const char *target[] = {"EPSG:25832", "EPSG:4326", "EPSG:4326", ""};
    for (int i = 0; i < 10; ++i) {
        for (int j = 0; j < 4; ++j) {
            PJ_CONTEXT *ctx = proj_context_create();
            assert(ctx);
            proj_context_set_enable_network(ctx, 0);
            PJ *invalid = proj_create_crs_to_crs(ctx, source[j], target[j], NULL);
            assert(!invalid);
            assert(proj_context_errno(ctx) != 0);
            PJ *valid = proj_create_crs_to_crs(ctx, "EPSG:4326", "EPSG:25832", NULL);
            assert(valid);
            proj_destroy(valid);
            proj_context_destroy(ctx);
        }
    }
    puts("PASS: all 40 invalid CRS rejections and 40 valid recoveries");
    return 0;
}
