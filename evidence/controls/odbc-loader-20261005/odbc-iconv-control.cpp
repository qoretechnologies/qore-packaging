// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <iconv.h>
#include <sql.h>
#include <sqlext.h>
#include <dlfcn.h>
#include <cstdio>
#include <cstdlib>
#include <string>
int main(int argc, char** argv) {
    if (argc != 2) { return 2; }
    void* lib = dlopen("libodbc.so.2", RTLD_LAZY | RTLD_GLOBAL);
    if (!lib) { return 3; }
#define LOAD(name) auto name = reinterpret_cast<decltype(&::name)>(dlsym(lib, #name)); if (!name) { return 4; }
    LOAD(SQLAllocHandle) LOAD(SQLSetEnvAttr) LOAD(SQLDriverConnectA) LOAD(SQLDisconnect) LOAD(SQLFreeHandle)
    std::string conn = "DRIVER=/usr/lib64/psqlodbcw.so;Server=";
    conn += std::getenv("PGHOST");
    conn += ";Port=5432;Database=postgres;UID=qore_test";
    for (int n = 0; n < std::atoi(argv[1]); ++n) {
        SQLHENV env = SQL_NULL_HENV;
        SQLHDBC dbc = SQL_NULL_HDBC;
        if (!SQL_SUCCEEDED(SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &env))) { return 5; }
        if (!SQL_SUCCEEDED(SQLSetEnvAttr(env, SQL_ATTR_ODBC_VERSION, reinterpret_cast<SQLPOINTER>(SQL_OV_ODBC3), 0))) { return 6; }
        if (!SQL_SUCCEEDED(SQLAllocHandle(SQL_HANDLE_DBC, env, &dbc))) { return 7; }
        if (!SQL_SUCCEEDED(SQLDriverConnectA(dbc, nullptr, reinterpret_cast<SQLCHAR*>(&conn[0]), SQL_NTS,
                nullptr, 0, nullptr, SQL_DRIVER_NOPROMPT))) { return 8; }
        iconv_t conv = iconv_open("US-ASCII", "ISO-8859-1");
        if (conv == (iconv_t)-1) { return 13; }
        char input[] = "1.25", output[32] = {};
        char* in = input;
        char* out = output;
        size_t in_left = 4, out_left = sizeof(output);
        if (iconv(conv, &in, &in_left, &out, &out_left) == (size_t)-1 || in_left) { return 14; }
        if (iconv_close(conv)) { return 15; }
        if (!SQL_SUCCEEDED(SQLDisconnect(dbc))) { return 9; }
        if (!SQL_SUCCEEDED(SQLFreeHandle(SQL_HANDLE_DBC, dbc))) { return 10; }
        if (!SQL_SUCCEEDED(SQLFreeHandle(SQL_HANDLE_ENV, env))) { return 11; }
    }
    // Deliberately retain the driver-manager handle until process teardown, as Qore does.
    return 0;
}
