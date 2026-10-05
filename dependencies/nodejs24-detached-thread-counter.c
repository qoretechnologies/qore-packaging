/* Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT */
#define _GNU_SOURCE
#include <assert.h>
#include <dlfcn.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stddef.h>

static atomic_uint detached_creations;
static pthread_once_t resolve_once = PTHREAD_ONCE_INIT;
static int (*real_pthread_create)(pthread_t *, const pthread_attr_t *,
                                 void *(*)(void *), void *);

static void resolve_create(void) {
    *(void **)(&real_pthread_create) = dlsym(RTLD_NEXT, "pthread_create");
    assert(real_pthread_create != NULL);
}

unsigned int qore_detached_thread_count(void) {
    return atomic_load(&detached_creations);
}

int pthread_create(pthread_t *thread, const pthread_attr_t *attributes,
                   void *(*start)(void *), void *argument) {
    assert(pthread_once(&resolve_once, resolve_create) == 0);
    int result = real_pthread_create(thread, attributes, start, argument);
    if (result == 0 && attributes != NULL) {
        int detached;
        assert(pthread_attr_getdetachstate(attributes, &detached) == 0);
        if (detached == PTHREAD_CREATE_DETACHED) {
            atomic_fetch_add(&detached_creations, 1);
        }
    }
    return result;
}
