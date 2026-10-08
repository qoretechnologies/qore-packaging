// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include <qore/Qore.h>
#include <cstdio>
#include <string>
int main() {
    qore_init(QL_MIT, "UTF-8", false, QLO_DISABLE_SIGNAL_HANDLING);
    int status = 0;
    {
        ExceptionSink xsink;
        ReferenceHolder<QoreHashNode> hash(new QoreHashNode(autoTypeInfo), &xsink);
        std::string bytes(1024 * 1024, 'a');
        hash->setKeyValue(bytes.c_str(), QoreValue(int64(7)), &xsink);
        QoreString key(bytes.data(), bytes.size(), QCS_ISO_8859_1);
        bool exists = false;
        const int cancel = qore_cancel_thread(q_gettid(), "hash scan control");
        QoreValue value = hash->getKeyValueExistence(key, exists, &xsink);
        bool caught = static_cast<bool>(xsink);
        xsink.clear();
        bool pending = qore_check_cancel(&xsink, "post-lookup control");
        xsink.clear();
        qore_clear_thread_cancel();
        std::printf("cancel=%d lookup_cancelled=%d pending_after=%d exists=%d value=%lld\n",
            cancel, caught, pending, exists, static_cast<long long>(value.getAsBigInt()));
        status = cancel || !pending ? 2 : caught ? 0 : 1;
    }
    qore_cleanup();
    return status;
}
