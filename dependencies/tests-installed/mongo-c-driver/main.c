/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * SPDX-License-Identifier: MIT
 * Exercise the installed shared BSON and MongoDB SDKs without a server. */
#include <mongoc/mongoc.h>
#include <stdio.h>
#include <string.h>

int main(void) {
    int result = 1;
    bson_error_t error;
    bson_t *document = NULL;
    mongoc_client_t *client = NULL;
    bson_t view;
    bson_iter_t iter;
    const char *appname = NULL;
    const uint8_t *bytes = NULL;
    uint32_t length = 0;

    mongoc_init();
    document = bson_new_from_json((const uint8_t *)"{\"nested\":{\"value\":42}}", -1, &error);
    if (!document || !bson_iter_init_find(&iter, document, "nested")) {
        goto cleanup;
    }
    bson_iter_document(&iter, &length, &bytes);
    if (!bson_init_static(&view, bytes, length)) {
        goto cleanup;
    }
    if (view.len != length || view.len <= 5 || !bson_iter_init_find(&iter, &view, "value")
            || !BSON_ITER_HOLDS_INT32(&iter) || bson_iter_int32(&iter) != 42) {
        bson_destroy(&view);
        goto cleanup;
    }
    bson_destroy(&view);
    client = mongoc_client_new("mongodb://127.0.0.1:27017/?appname=qore-rpm-sdk-test");
    if (client) {
        appname = mongoc_uri_get_appname(mongoc_client_get_uri(client));
    }
    if (!appname || strcmp(appname, "qore-rpm-sdk-test")) {
        goto cleanup;
    }
    printf("Installed BSON %s / MongoDB C %s SDK passed\n", bson_get_version(), mongoc_get_version());
    result = 0;

cleanup:
    if (client) {
        mongoc_client_destroy(client);
    }
    if (document) {
        bson_destroy(document);
    }
    mongoc_cleanup();
    if (result) {
        fprintf(stderr, "Installed BSON/MongoDB SDK validation failed\n");
    }
    return result;
}
