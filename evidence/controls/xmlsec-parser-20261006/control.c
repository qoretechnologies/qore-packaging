/* Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT */
#include <stdio.h>
#include <openssl/crypto.h>
#include <string.h>
#include <libxml/parser.h>
#include <libxslt/xslt.h>
#include <xmlsec/xmlsec.h>
#include <xmlsec/crypto.h>
#include <xmlsec/templates.h>
#include <xmlsec/xmlenc.h>
#include <xmlsec/xmltree.h>

static int check(const xmlSecByte* bytes, xmlSecSize size, int valid) {
    int result = 1;
    xmlDocPtr doc = NULL;
    xmlSecKeyPtr key = NULL;
    xmlSecEncCtxPtr encryption = NULL, decryption = NULL;
    xmlNodePtr parent = NULL, tmpl = NULL;
    doc = xmlNewDoc(BAD_CAST "1.0");
    if (!doc) { goto done; }
    parent = xmlNewNode(NULL, BAD_CAST "parent");
    if (!parent) { goto done; }
    xmlDocSetRootElement(doc, parent);
    tmpl = xmlSecTmplEncDataCreate(doc, xmlSecTransformAes256CbcId, NULL,
                                 xmlSecTypeEncElement, NULL, NULL);
    if (!tmpl) { goto done; }
    xmlAddChild(parent, tmpl);
    if (!xmlSecTmplEncDataEnsureCipherValue(tmpl)) { goto done; }
    key = xmlSecKeyGenerate(xmlSecKeyDataAesId, 256, xmlSecKeyDataTypeSession);
    encryption = xmlSecEncCtxCreate(NULL);
    decryption = xmlSecEncCtxCreate(NULL);
    if (!key || !encryption || !decryption) { goto done; }
    encryption->encKey = xmlSecKeyDuplicate(key);
    decryption->encKey = xmlSecKeyDuplicate(key);
    if (!encryption->encKey || !decryption->encKey) { goto done; }
    if (xmlSecEncCtxBinaryEncrypt(encryption, tmpl, bytes, size) < 0) { goto done; }
    int rc = xmlSecEncCtxDecrypt(decryption, tmpl);
    if (valid) {
        xmlNodePtr child = xmlSecGetNextElementNode(parent->children);
        if (rc != 0 || !decryption->resultReplaced || !child ||
            !xmlStrEqual(child->name, BAD_CAST "value")) { goto done; }
        xmlChar* value = xmlNodeGetContent(child);
        int same = value && xmlStrEqual(value, BAD_CAST "roundtrip");
        xmlFree(value);
        if (!same) { goto done; }
    } else {
        /* Crypto succeeded. XML replacement must reject malformed plaintext. */
        if (rc >= 0 || !decryption->result || decryption->resultReplaced ||
            xmlSecBufferGetSize(decryption->result) != size ||
            memcmp(xmlSecBufferGetData(decryption->result), bytes, size) != 0) { goto done; }
    }
    result = 0;
done:
    if (encryption) { xmlSecEncCtxDestroy(encryption); }
    if (decryption) { xmlSecEncCtxDestroy(decryption); }
    if (key) { xmlSecKeyDestroy(key); }
    if (doc) { xmlFreeDoc(doc); }
    return result;
}
int main(void) {
    int status = 1;
    xmlInitParser();
    if (xmlSecInit() < 0) { return 2; }
    if (xmlSecCryptoAppInit(NULL) < 0) { xmlSecShutdown(); return 3; }
    if (xmlSecCryptoInit() < 0) { xmlSecCryptoAppShutdown(); xmlSecShutdown(); return 4; }
    const xmlSecByte good[] = "<value>roundtrip</value>";
    const xmlSecByte bad[] = {'<', 'v', '>', 0x1e, 0xff, '&', 'x', '<', '/', 'v', '>'};
    for (unsigned i = 0; i < 10; ++i) {
        if (check(good, sizeof(good) - 1, 1) || check(bad, sizeof(bad), 0)) { goto done; }
    }
    puts("20 valid/malformed decrypted XML controls passed");
    status = 0;
done:
    xmlSecCryptoShutdown();
    xmlSecCryptoAppShutdown();
    xmlSecShutdown();
    xsltCleanupGlobals();
    xmlCleanupParser();
    OPENSSL_cleanup();
    return status;
}
