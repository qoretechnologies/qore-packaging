/* Copyright (C) 2026 Qore Technologies, s.r.o.
 * SPDX-License-Identifier: MIT
 * Exercise the real plugin's private cipher initialization and cleanup paths.
 */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/evp.h>
#include <openssl/provider.h>
#include <openssl/err.h>

static int fail_at;
static int calls;
static int fail(void) { return ++calls == fail_at; }
static void *test_malloc(size_t size) { return fail() ? NULL : malloc(size); }
static OSSL_LIB_CTX *test_libctx_new(void) { return fail() ? NULL : OSSL_LIB_CTX_new(); }
static OSSL_PROVIDER *test_provider_load(OSSL_LIB_CTX *ctx, const char *name) {
    return fail() ? NULL : OSSL_PROVIDER_load(ctx, name);
}
static EVP_CIPHER *test_cipher_fetch(OSSL_LIB_CTX *ctx, const char *name, const char *props) {
    return fail() ? NULL : EVP_CIPHER_fetch(ctx, name, props);
}
static EVP_CIPHER_CTX *test_cipher_ctx_new(void) { return fail() ? NULL : EVP_CIPHER_CTX_new(); }
static int test_encrypt_init(EVP_CIPHER_CTX *ctx, const EVP_CIPHER *cipher, ENGINE *impl,
                             const unsigned char *key, const unsigned char *iv) {
    return fail() ? 0 : EVP_EncryptInit_ex(ctx, cipher, impl, key, iv);
}
static int test_decrypt_init(EVP_CIPHER_CTX *ctx, const EVP_CIPHER *cipher, ENGINE *impl,
                             const unsigned char *key, const unsigned char *iv) {
    return fail() ? 0 : EVP_DecryptInit_ex(ctx, cipher, impl, key, iv);
}
#define OSSL_LIB_CTX_new test_libctx_new
#define OSSL_PROVIDER_load test_provider_load
#define EVP_CIPHER_fetch test_cipher_fetch
#define EVP_CIPHER_CTX_new test_cipher_ctx_new
#define EVP_EncryptInit_ex test_encrypt_init
#define EVP_DecryptInit_ex test_decrypt_init
#include "plugins/digestmd5.c"
#undef EVP_CIPHER_fetch

static void check_clean(context_t *ctx) {
    assert(ctx->crypto.enc_ctx == NULL);
    assert(ctx->crypto.dec_ctx == NULL);
    assert(ctx->crypto.libctx == NULL);
}

int main(void) {
    sasl_utils_t utils = {0};
    unsigned char key[16] = "test-cipher-key";
    unsigned char digest[16] = "test-digest";
    const char plaintext[] = "SASL protected LDAP response";
    char ciphertext[128], decoded[128];
    unsigned int encrypted_len, decoded_len;
    int maximum_calls;
    utils.malloc = test_malloc;
    utils.free = free;
    /* Private providers must not activate legacy ciphers for other users. */
    assert(EVP_CIPHER_fetch(NULL, "RC4", "") == NULL);
    ERR_clear_error();
    context_t ctx = {0};
    ctx.utils = &utils;
    assert(init_rc4(&ctx, key, key) == SASL_OK);
    maximum_calls = calls;
    assert(maximum_calls == 9);
    assert(enc_rc4(&ctx, plaintext, sizeof(plaintext), digest, ciphertext, &encrypted_len) == SASL_OK);
    assert(encrypted_len == sizeof(plaintext) + 10);
    assert(dec_rc4(&ctx, ciphertext, encrypted_len, digest, decoded, &decoded_len) == SASL_OK);
    assert(decoded_len == sizeof(plaintext));
    assert(memcmp(decoded, plaintext, sizeof(plaintext)) == 0);
    assert(memcmp(decoded + decoded_len, digest, 10) == 0);
    free_rc4(&ctx);
    free_rc4(&ctx);
    check_clean(&ctx);
    for (int point = 1; point <= maximum_calls; ++point) {
        memset(&ctx, 0, sizeof(ctx));
        ctx.utils = &utils;
        fail_at = point;
        calls = 0;
        int rc = init_rc4(&ctx, key, key);
        /* RC4 belongs to legacy; the default provider is optional for it. */
        if (point == 4) {
            assert(rc == SASL_OK);
        } else {
            assert(rc == SASL_FAIL || rc == SASL_NOMEM);
            check_clean(&ctx);
        }
        free_rc4(&ctx);
        free_rc4(&ctx);
        check_clean(&ctx);
        ERR_clear_error();
    }
    assert(EVP_CIPHER_fetch(NULL, "RC4", "") == NULL);
    ERR_clear_error();
    puts("PASS: encrypted round trip, nine initialization failures, repeated cleanup and private providers");
    return 0;
}
