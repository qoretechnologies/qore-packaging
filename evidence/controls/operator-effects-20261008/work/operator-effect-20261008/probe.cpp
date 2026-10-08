// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
#define _QORE_LIB_INTERN
#include <qore/Qore.h>
#include <qore/RuntimeConfig.h>
#include <cstdio>
#include <stdexcept>
template <typename Base>
class Fixture : public Base {
public:
    using Base::Base;
    ~Fixture() override = default;
    QoreString* getAsString(bool& del, int, ExceptionSink*) const override {
        del = true;
        return new QoreString("effect fixture");
    }
    int getAsString(QoreString& str, int, ExceptionSink*) const override {
        str.concat("effect fixture");
        return 0;
    }
    const char* getTypeName() const override { return "effect fixture"; }
    QoreOperatorNode* copyBackground(ExceptionSink*) const override {
        throw std::logic_error("fixture does not support background copying");
    }
protected:
    QoreValue evalImpl(bool& needs_deref, ExceptionSink*) const override {
        needs_deref = false;
        return QoreValue();
    }
    int parseInitImpl(QoreValue&, QoreParseContext&) override {
        throw std::logic_error("fixture does not support parsing");
    }
};
int AbstractQoreNode::parseInit(QoreValue& val, QoreParseContext& parse_context) {
    // no action taken by default
    return 0;
}
int main() {
    qore_init(QL_MIT, "UTF-8", false, QLO_DISABLE_SIGNAL_HANDLING);
    {
        Fixture<QoreSingleExpressionOperatorNode<LValueOperatorNode>> x(nullptr,QoreValue());
        Fixture<QoreSingleExpressionOperatorNode<>> y(nullptr,QoreValue());
        std::printf("%d %d\n",x.hasEffectAsRoot(),y.hasEffectAsRoot());
    }
    qore_cleanup();
}
