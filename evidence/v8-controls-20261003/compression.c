/* Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT */
#include <assert.h>
#include <openssl/ssl.h>
#include <openssl/crypto.h>
int main(int argc, char **argv) {
    (void)argv;
    assert(OPENSSL_init_ssl(0, NULL) == 1);
    STACK_OF(SSL_COMP) *methods = SSL_COMP_get_compression_methods();
    assert(methods != NULL);
    assert(sk_SSL_COMP_num(methods) == 1);
    if (argc == 1) {
        sk_SSL_COMP_zero(methods);
    } else {
        SSL_COMP *method;
        while ((method = sk_SSL_COMP_pop(methods)) != NULL) {
            OPENSSL_free(method);
        }
    }
    assert(sk_SSL_COMP_num(methods) == 0);
    OPENSSL_cleanup();
    return 0;
}
