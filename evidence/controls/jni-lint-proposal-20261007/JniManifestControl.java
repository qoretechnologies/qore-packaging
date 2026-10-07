// Copyright 2026 Qore Technologies, s.r.o.; SPDX-License-Identifier: MIT
import java.io.StringReader;
import java.io.StringWriter;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.SAXParserFactory;
import net.rootdev.javardfa.uri.IRIResolver;
import org.apache.jena.rdf.model.Model;
import org.apache.xml.serializer.OutputPropertiesFactory;
import org.apache.xml.serializer.Serializer;
import org.apache.xml.serializer.SerializerFactory;
import org.odftoolkit.odfdom.doc.OdfSpreadsheetDocument;
import org.odftoolkit.odfdom.pkg.OdfFileDom;
import org.odftoolkit.odfdom.pkg.rdfa.JenaSink;
import org.odftoolkit.odfdom.pkg.rdfa.SAXRDFaParser;
import org.xml.sax.ContentHandler;
import org.xml.sax.InputSource;
import org.xml.sax.XMLReader;
import org.xml.sax.helpers.AttributesImpl;

public final class JniManifestControl {
    private static int checks;

    private static void check(boolean value, String description) {
        if (!value) {
            throw new AssertionError(description);
        }
        ++checks;
    }

    private static void origin(Class<?> type, String filename) {
        String location = type.getProtectionDomain().getCodeSource().getLocation().toString();
        check(location.endsWith("/" + filename), type + ": " + location);
        System.out.println(type.getName() + " loaded from " + location);
    }

    public static void main(String[] args) throws Exception {
        origin(IRIResolver.class, "java-rdfa-1.0.0-BETA1.jar");
        origin(org.apache.jena.iri.IRIFactory.class, "jena-iri-4.10.0.jar");
        origin(SerializerFactory.class, "serializer-2.7.3.jar");
        check("java.xml".equals(InputSource.class.getModule().getName()), "XML API comes from the JDK");
        IRIResolver resolver = new IRIResolver();
        check(resolver.resolve("https://example.org/reports/", "../invoices/2026")
                .equals("https://example.org/invoices/2026"), "relative IRI resolution");
        check(resolver.resolve("https://example.org/", "report#résumé")
                .equals("https://example.org/report#résumé"), "Unicode IRI resolution");
        try {
            resolver.resolve(null, "item");
            throw new AssertionError("null base accepted");
        } catch (RuntimeException expected) {
            check(expected.getMessage().equals("Base is null."), "invalid IRI input rejected");
        }
        for (int i = 0; i < 20; ++i) {
            String text = "invoice " + i + " & résumé";
            try (OdfSpreadsheetDocument document = OdfSpreadsheetDocument.newSpreadsheetDocument()) {
                OdfFileDom dom = document.getContentDom();
                JenaSink sink = new JenaSink(dom);
                sink.setContextNode(dom.getDocumentElement());
                SAXRDFaParser parser = SAXRDFaParser.createInstance(sink);
                SAXParserFactory factory = SAXParserFactory.newInstance();
                factory.setNamespaceAware(true);
                XMLReader reader = factory.newSAXParser().getXMLReader();
                reader.setContentHandler(parser);
                String xml = "<root xmlns:dc=\"http://purl.org/dc/elements/1.1/\">"
                        + "<p about=\"https://example.org/invoice/" + i + "\" property=\"dc:title\">"
                        + text.replace("&", "&amp;") + "</p></root>";
                InputSource input = new InputSource(new StringReader(xml));
                input.setSystemId("https://example.org/");
                reader.parse(input);
                Model model = dom.getInContentMetadataCache().get(dom.getDocumentElement());
                check(model != null && model.size() == 1, "exactly one RDFa triple");
                check(model.contains(model.createResource("https://example.org/invoice/" + i),
                        model.createProperty("http://purl.org/dc/elements/1.1/title"), text),
                        "ODF RDFa preserves invoice title");
            }
            StringWriter output = new StringWriter();
            Serializer serializer = SerializerFactory.getSerializer(
                    OutputPropertiesFactory.getDefaultMethodProperties("xml"));
            serializer.setWriter(output);
            ContentHandler handler = serializer.asContentHandler();
            handler.startDocument();
            handler.startElement("", "invoice", "invoice", new AttributesImpl());
            char[] chars = text.toCharArray();
            handler.characters(chars, 0, chars.length);
            handler.endElement("", "invoice", "invoice");
            handler.endDocument();
            String parsed = DocumentBuilderFactory.newDefaultInstance().newDocumentBuilder()
                    .parse(new InputSource(new StringReader(output.toString())))
                    .getDocumentElement().getTextContent();
            check(parsed.equals(text), "serializer XML API preserves markup and Unicode");
        }
        System.out.println("PASS: " + checks + " private JAR and JDK XML API checks");
    }
}
