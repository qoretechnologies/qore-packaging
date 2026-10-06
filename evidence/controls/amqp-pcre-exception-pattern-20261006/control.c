/* Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT */
#define PCRE2_CODE_UNIT_WIDTH 8
#include <pcre2.h>
#include <valgrind/memcheck.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct Case { const char* pattern; const char* subject; uint32_t compile_options; size_t offset; uint32_t options; int result; };
static const struct Case cases[]={
    {"TEST-.*EXCEPTION", "AMQP-DELIVERY-ERROR", 524288, 0, 0, -1},
    {"TEST-.*EXCEPTION", "", 524288, 0, 0, -1},
    {"TEST-.*EXCEPTION", "TEST-", 524288, 0, 0, -1},
    {"TEST-.*EXCEPTION", "TEST-EXCEPTION", 524288, 0, 0, 1},
    {"TEST-.*EXCEPTION", "TEST-X-EXCEPTION", 524288, 0, 0, 1},
    {"TEST-.*EXCEPTION", "preTEST-X-EXCEPTIONpost", 524288, 0, 0, 1},
    {"TEST-.*EXCEPTION", "TEST-X\nEXCEPTION", 524288, 0, 0, -1},
    {"TEST-.*EXCEPTION", "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXTEST-YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYEXCEPTION", 524288, 0, 0, 1},
    {"TEST-.*EXCEPTION", "TEST-X-EXCEPTION\n", 524288, 0, 0, 1},
    {"TEST-.*EXCEPTION", "TEST-X-EXCEPTIO", 524288, 0, 0, -1},
};
int main(int argc,char** argv) {
    if (argc!=2 || (strcmp(argv[1],"defined") && strcmp(argv[1],"undefined"))) { return 2; }
    int undefined=!strcmp(argv[1],"undefined");
    size_t checks=0;
    for (size_t i=0;i<sizeof(cases)/sizeof(cases[0]);++i) {
        const struct Case* c=&cases[i];
        int error,status=1;
        PCRE2_SIZE error_offset;
        size_t length=strlen(c->subject), capacity=length+64;
        pcre2_code* code=pcre2_compile((PCRE2_SPTR)c->pattern,PCRE2_ZERO_TERMINATED,c->compile_options,&error,&error_offset,NULL);
        if (!code) { return 3; }
        pcre2_match_data* reference=pcre2_match_data_create_from_pattern(code,NULL);
        pcre2_match_data* actual=pcre2_match_data_create_from_pattern(code,NULL);
        char* buffer=malloc(capacity);
        if (!reference || !actual || !buffer) { goto cleanup; }
        if (pcre2_jit_compile(code,PCRE2_JIT_COMPLETE)) { goto cleanup; }
        int expected=pcre2_match(code,(PCRE2_SPTR)c->subject,length,c->offset,c->options|PCRE2_NO_JIT,reference,NULL);
        if (expected!=c->result) { fprintf(stderr,"Case %zu interpreter %d != %d\n",i,expected,c->result); goto cleanup; }
        for (size_t shift=0;shift<16;++shift) {
            for (unsigned padding=0;padding<256;++padding) {
                memset(buffer,(int)padding,capacity);
                if (undefined) { (void)VALGRIND_MAKE_MEM_UNDEFINED(buffer,capacity); }
                memcpy(buffer+shift,c->subject,length+1);
                int result=pcre2_match(code,(PCRE2_SPTR)(buffer+shift),length,c->offset,c->options,actual,NULL);
                if (result!=expected) { fprintf(stderr,"Case %zu shift %zu padding %u match %d != %d\n",i,shift,padding,result,expected); goto cleanup; }
                if (result>0 && memcmp(pcre2_get_ovector_pointer(actual),pcre2_get_ovector_pointer(reference),2*(size_t)result*sizeof(PCRE2_SIZE))) { fprintf(stderr,"Capture mismatch in case %zu\n",i); goto cleanup; }
                ++checks;
            }
        }
        status=0;
cleanup:
        free(buffer);
        pcre2_match_data_free(actual);
        pcre2_match_data_free(reference);
        pcre2_code_free(code);
        if (status) { return status; }
    }
    printf("%zu PCRE2 result/capture checks passed across %zu inputs, 16 alignments and 256 padding values (%s)\n",checks,sizeof(cases)/sizeof(cases[0]),argv[1]);
    return 0;
}
