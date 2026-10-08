// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <qore/Qore.h>
#include <cstdio>
static void lookup() {
    ExceptionSink xsink;
    ReferenceHolder<QoreHashNode> holder(new QoreHashNode(autoTypeInfo), &xsink);
    QoreHashNode& accounts = **holder;
    accounts.setKeyValue("caf\xc3\xa9", QoreValue(int64(73)), &xsink);
        QoreString account_key("caf\xe9", QCS_ISO_8859_1);
        bool found;
        QoreValue account = accounts.getKeyValueExistence(account_key, found, &xsink);
        if (!xsink && found) {
            printf("Account balance: %lld\n", static_cast<long long>(account.getAsBigInt()));
        }
}
int main() {
    qore_init(QL_MIT, "UTF-8", false, QLO_DISABLE_SIGNAL_HANDLING);
    lookup();
    qore_cleanup();
}
