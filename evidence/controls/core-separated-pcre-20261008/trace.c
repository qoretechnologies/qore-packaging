/* Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT */
#define _GNU_SOURCE
#define PCRE2_CODE_UNIT_WIDTH 8
#include <pcre2.h>
#include <dlfcn.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
pcre2_code* pcre2_compile_8(PCRE2_SPTR p, PCRE2_SIZE n, uint32_t options, int* error, PCRE2_SIZE* offset, pcre2_compile_context* context) {
    pcre2_code* (*compile)(PCRE2_SPTR,PCRE2_SIZE,uint32_t,int*,PCRE2_SIZE*,pcre2_compile_context*) = dlsym(RTLD_NEXT,"pcre2_compile_8");
    if (!compile) { abort(); }
    pcre2_code* code=compile(p,n,options,error,offset,context);
    fprintf(stderr,"PCRE-COMPILE %p options=%u pattern=%.*s\n",(void*)code,options,(int)(n==PCRE2_ZERO_TERMINATED?strlen((const char*)p):n),p);
    return code;
}
int pcre2_match_8(const pcre2_code* code,PCRE2_SPTR subject,PCRE2_SIZE length,PCRE2_SIZE offset,uint32_t options,pcre2_match_data* data,pcre2_match_context* context) {
    int (*match)(const pcre2_code*,PCRE2_SPTR,PCRE2_SIZE,PCRE2_SIZE,uint32_t,pcre2_match_data*,pcre2_match_context*)=dlsym(RTLD_NEXT,"pcre2_match_8");
    if (!match) { abort(); }
    fprintf(stderr,"PCRE-MATCH %p len=%zu start=%zu options=%u subject=%.*s\n",(void*)code,length,offset,options,(int)length,subject);
    int result=match(code,subject,length,offset,options,data,context);
    fprintf(stderr,"PCRE-RESULT %p result=%d\n",(void*)code,result);
    return result;
}
