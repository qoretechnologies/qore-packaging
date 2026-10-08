// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#include "bson_conversion.h"
#include <cstdio>
int main() {
    qore_init(QL_MIT, "UTF-8", false, QLO_DISABLE_SIGNAL_HANDLING);
    int status = 0;
    {
        ExceptionSink xsink;
        ReferenceHolder<QoreListNode> list(new QoreListNode(autoTypeInfo), &xsink);
        for (int i = 0; i < 101; ++i) {
            if (i && !(i % 100) && qore_check_cancel(&xsink, "preparing cancellation fixture")) { status = 2; break; }
            list->push(QoreValue(int64(i)), &xsink);
        }
        bson_t doc;
        bson_init(&doc);
        if (xsink || qore_cancel_thread(q_gettid(), "BSON array control")) { status = 2; }
        if (!status) {
            int rc = qore_list_to_bson_array(&doc, "items", *list, &xsink);
            std::printf("conversion=%d exception=%d elements=%u\n", rc, bool(xsink), bson_count_keys(&doc));
            if (rc != -1 || !xsink) { status = 1; }
        }
        qore_clear_thread_cancel();
        xsink.clear();
        bson_destroy(&doc);
    }
    qore_cleanup();
    return status;
}
