/* Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT */
#define PCRE2_CODE_UNIT_WIDTH 8
#include <pcre2.h>
#include <valgrind/memcheck.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
struct Case { const char* pattern; const char* subject; uint32_t compile_options; size_t offset; uint32_t options; int result; };
static const struct Case cases[]={
    {"[-_]", "int", 524288, 0, 0, -1},
    {"^.?soft", "int", 524288, 0, 0, -1},
    {"[-_]", "string", 524288, 0, 0, -1},
    {"^.?soft", "string", 524288, 0, 0, -1},
    {"[-_]", "bool", 524288, 0, 0, -1},
    {"^.?soft", "bool", 524288, 0, 0, -1},
    {"[-_]", "float", 524288, 0, 0, -1},
    {"^.?soft", "float", 524288, 0, 0, -1},
    {"[-_]", "number", 524288, 0, 0, -1},
    {"^.?soft", "number", 524288, 0, 0, -1},
    {"[-_]", "binary", 524288, 0, 0, -1},
    {"^.?soft", "binary", 524288, 0, 0, -1},
    {"[-_]", "list<auto>", 524288, 0, 0, -1},
    {"^.?soft", "list<auto>", 524288, 0, 0, -1},
    {"[-_]", "hash<auto>", 524288, 0, 0, -1},
    {"^.?soft", "hash<auto>", 524288, 0, 0, -1},
    {"[-_]", "object", 524288, 0, 0, -1},
    {"^.?soft", "object", 524288, 0, 0, -1},
    {"[-_]", "date", 524288, 0, 0, -1},
    {"^.?soft", "date", 524288, 0, 0, -1},
    {"[-_]", "null", 524288, 0, 0, -1},
    {"^.?soft", "null", 524288, 0, 0, -1},
    {"[-_]", "nothing", 524288, 0, 0, -1},
    {"^.?soft", "nothing", 524288, 0, 0, -1},
    {"[-_]", "base64binary", 524288, 0, 0, -1},
    {"^.?soft", "base64binary", 524288, 0, 0, -1},
    {"[-_]", "base64urlbinary", 524288, 0, 0, -1},
    {"^.?soft", "base64urlbinary", 524288, 0, 0, -1},
    {"[-_]", "hexbinary", 524288, 0, 0, -1},
    {"^.?soft", "hexbinary", 524288, 0, 0, -1},
    {"[-_]", "data", 524288, 0, 0, -1},
    {"^.?soft", "data", 524288, 0, 0, -1},
    {"[-_]", "timeout", 524288, 0, 0, -1},
    {"^.?soft", "timeout", 524288, 0, 0, -1},
    {"[-_]", "*timeout", 524288, 0, 0, -1},
    {"^.?soft", "*timeout", 524288, 0, 0, -1},
    {"[-_]", "softint", 524288, 0, 0, -1},
    {"^.?soft", "softint", 524288, 0, 0, 1},
    {"[-_]", "softstring", 524288, 0, 0, -1},
    {"^.?soft", "softstring", 524288, 0, 0, 1},
    {"[-_]", "softbool", 524288, 0, 0, -1},
    {"^.?soft", "softbool", 524288, 0, 0, 1},
    {"[-_]", "softfloat", 524288, 0, 0, -1},
    {"^.?soft", "softfloat", 524288, 0, 0, 1},
    {"[-_]", "softnumber", 524288, 0, 0, -1},
    {"^.?soft", "softnumber", 524288, 0, 0, 1},
    {"[-_]", "softdate", 524288, 0, 0, -1},
    {"^.?soft", "softdate", 524288, 0, 0, 1},
    {"[-_]", "softlist", 524288, 0, 0, -1},
    {"^.?soft", "softlist", 524288, 0, 0, 1},
    {"[-_]", "*softint", 524288, 0, 0, -1},
    {"^.?soft", "*softint", 524288, 0, 0, 1},
    {"[-_]", "*softstring", 524288, 0, 0, -1},
    {"^.?soft", "*softstring", 524288, 0, 0, 1},
    {"[-_]", "*softbool", 524288, 0, 0, -1},
    {"^.?soft", "*softbool", 524288, 0, 0, 1},
    {"[-_]", "*softfloat", 524288, 0, 0, -1},
    {"^.?soft", "*softfloat", 524288, 0, 0, 1},
    {"[-_]", "*softnumber", 524288, 0, 0, -1},
    {"^.?soft", "*softnumber", 524288, 0, 0, 1},
    {"[-_]", "*softdate", 524288, 0, 0, -1},
    {"^.?soft", "*softdate", 524288, 0, 0, 1},
    {"[-_]", "*softlist", 524288, 0, 0, -1},
    {"^.?soft", "*softlist", 524288, 0, 0, 1},
    {"[-_]", "auto", 524288, 0, 0, -1},
    {"^.?soft", "auto", 524288, 0, 0, -1},
    {"[-_]", "*int", 524288, 0, 0, -1},
    {"^.?soft", "*int", 524288, 0, 0, -1},
    {"[-_]", "*string", 524288, 0, 0, -1},
    {"^.?soft", "*string", 524288, 0, 0, -1},
    {"[-_]", "*bool", 524288, 0, 0, -1},
    {"^.?soft", "*bool", 524288, 0, 0, -1},
    {"[-_]", "*float", 524288, 0, 0, -1},
    {"^.?soft", "*float", 524288, 0, 0, -1},
    {"[-_]", "*number", 524288, 0, 0, -1},
    {"^.?soft", "*number", 524288, 0, 0, -1},
    {"[-_]", "*binary", 524288, 0, 0, -1},
    {"^.?soft", "*binary", 524288, 0, 0, -1},
    {"[-_]", "*list<auto>", 524288, 0, 0, -1},
    {"^.?soft", "*list<auto>", 524288, 0, 0, -1},
    {"[-_]", "*hash<auto>", 524288, 0, 0, -1},
    {"^.?soft", "*hash<auto>", 524288, 0, 0, -1},
    {"[-_]", "*object", 524288, 0, 0, -1},
    {"^.?soft", "*object", 524288, 0, 0, -1},
    {"[-_]", "*date", 524288, 0, 0, -1},
    {"^.?soft", "*date", 524288, 0, 0, -1},
    {"[-_]", "*base64binary", 524288, 0, 0, -1},
    {"^.?soft", "*base64binary", 524288, 0, 0, -1},
    {"[-_]", "*base64urlbinary", 524288, 0, 0, -1},
    {"^.?soft", "*base64urlbinary", 524288, 0, 0, -1},
    {"[-_]", "*hexbinary", 524288, 0, 0, -1},
    {"^.?soft", "*hexbinary", 524288, 0, 0, -1},
    {"[-_]", "*data", 524288, 0, 0, -1},
    {"^.?soft", "*data", 524288, 0, 0, -1},
    {"[-_]", "*softlist<string>", 524288, 0, 0, -1},
    {"^.?soft", "*softlist<string>", 524288, 0, 0, 1},
    {"[-_]", "*list<string>", 524288, 0, 0, -1},
    {"^.?soft", "*list<string>", 524288, 0, 0, -1},
    {"//", "/", 524288, 0, 0, -1},
    {"\\{([^\\}]*)}", "/", 524288, 0, 0, -1},
    {"//", "/{address}", 524288, 0, 0, -1},
    {"\\{([^\\}]*)}", "/{address}", 524288, 0, 0, 2},
    {"\\{([^\\}]*)}", "/{address}", 524288, 9, 1073741824, -1},
    {"//", "/{address}/events", 524288, 0, 0, -1},
    {"\\{([^\\}]*)}", "/{address}/events", 524288, 0, 0, 2},
    {"\\{([^\\}]*)}", "/{address}/events", 524288, 9, 1073741824, -1},
    {"\\.qm$", "/results/test/AmqpDataProvider.qtest", 524288, 0, 0, -1},
    {"[-_]", "test-conn", 524288, 0, 0, 1},
    {"[-_]", "test-conn", 524288, 5, 1073741824, -1},
    {"`", "Test AMQP connection", 524288, 0, 0, -1},
    {"\\*\\*([^*]+)\\*\\*", "Test AMQP connection", 524288, 0, 0, -1},
    {"(^|[[:space:]])_([^_]+)_(?=[[:space:][:punct:]]|$)", "Test AMQP connection", 524288, 0, 0, -1},
    {"[\\n\\r]+$", "amqp://guest:guest@amqp-broker:5672", 524288, 0, 0, -1},
    {"\\.qm$", "/results/test/AmqpUtil.qtest", 524288, 0, 0, -1},
    {"[-_]", "", 524288, 0, 0, -1},
    {"[-_]", "-", 524288, 0, 0, 1},
    {"[-_]", "_", 524288, 0, 0, 1},
    {"[-_]", "x_y", 524288, 0, 0, 1},
    {"[-_]", "x-y", 524288, 0, 0, 1},
    {"[-_]", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx_", 524288, 0, 0, 1},
    {"^.?soft", "", 524288, 0, 0, -1},
    {"^.?soft", "soft", 524288, 0, 0, 1},
    {"^.?soft", "*soft", 524288, 0, 0, 1},
    {"^.?soft", "xsoft", 524288, 0, 0, 1},
    {"^.?soft", "xxsoft", 524288, 0, 0, -1},
    {"^.?soft", "sof", 524288, 0, 0, -1},
    {"\\{([^\\}]*)}", "", 524288, 0, 0, -1},
    {"\\{([^\\}]*)}", "{}", 524288, 0, 0, 2},
    {"\\{([^\\}]*)}", "{x}", 524288, 0, 0, 2},
    {"\\{([^\\}]*)}", "{x", 524288, 0, 0, -1},
    {"\\{([^\\}]*)}", "x}", 524288, 0, 0, -1},
    {"\\{([^\\}]*)}", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx{value}", 524288, 0, 0, 2},
    {"//", "", 524288, 0, 0, -1},
    {"//", "/", 524288, 0, 0, -1},
    {"//", "//", 524288, 0, 0, 1},
    {"//", "///", 524288, 0, 0, 1},
    {"//", "a/b", 524288, 0, 0, -1},
    {"//", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx//", 524288, 0, 0, 1},
    {"`", "", 524288, 0, 0, -1},
    {"`", "`", 524288, 0, 0, 1},
    {"`", "a`b`c", 524288, 0, 0, 1},
    {"\\.qm$", "", 524288, 0, 0, -1},
    {"\\.qm$", ".qm", 524288, 0, 0, 1},
    {"\\.qm$", "a.qm", 524288, 0, 0, 1},
    {"\\.qm$", "a.qtest", 524288, 0, 0, -1},
    {"\\.qm$", "a.qmX", 524288, 0, 0, -1},
    {"\\*\\*([^*]+)\\*\\*", "", 524288, 0, 0, -1},
    {"\\*\\*([^*]+)\\*\\*", "**x**", 524288, 0, 0, 2},
    {"\\*\\*([^*]+)\\*\\*", "a**long words**b", 524288, 0, 0, 2},
    {"\\*\\*([^*]+)\\*\\*", "****", 524288, 0, 0, -1},
    {"\\*\\*([^*]+)\\*\\*", "**x*", 524288, 0, 0, -1},
    {"(^|[[:space:]])_([^_]+)_(?=[[:space:][:punct:]]|$)", "", 524288, 0, 0, -1},
    {"(^|[[:space:]])_([^_]+)_(?=[[:space:][:punct:]]|$)", "_x_", 524288, 0, 0, 3},
    {"(^|[[:space:]])_([^_]+)_(?=[[:space:][:punct:]]|$)", "a _long words_ z", 524288, 0, 0, 3},
    {"(^|[[:space:]])_([^_]+)_(?=[[:space:][:punct:]]|$)", "a_x_z", 524288, 0, 0, -1},
    {"(^|[[:space:]])_([^_]+)_(?=[[:space:][:punct:]]|$)", "_x", 524288, 0, 0, -1},
    {"[\\n\\r]+$", "", 524288, 0, 0, -1},
    {"[\\n\\r]+$", "abc", 524288, 0, 0, -1},
    {"[\\n\\r]+$", "abc\n", 524288, 0, 0, 1},
    {"[\\n\\r]+$", "abc\r\n", 524288, 0, 0, 1},
    {"[\\n\\r]+$", "abc\nX", 524288, 0, 0, -1},
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
