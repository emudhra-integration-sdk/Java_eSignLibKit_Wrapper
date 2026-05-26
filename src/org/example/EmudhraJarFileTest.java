package org.example;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Base64;

/**
 * Manual test harness for EmudhraJarFile.
 * Simulates exactly what Node.js does: pass JSON in, print JSON out.
 *
 * Update the constants at the top of the class before running.
 */
public class EmudhraJarFileTest {

    // ── Configure these before running ────────────────────────────────────────
    private static final String ASP_ID       = "YOUR_ASP_ID";
    private static final String ESIGN_URL    = "https://esign-uat.emudhra.com/eSignRequest";   // V2 (Aadhaar)
    private static final String ESIGN_URL_V2 = "https://esign-uat.emudhra.com/eSignPANRequest"; // V3 (PAN)

    private static final String PFX_PATH     = "D:/certs/Test-Class3DocumentSigner2014.pfx";
    private static final String PFX_PASSWORD = "emudhra";
    private static final String PFX_ALIAS    = "1";

    private static final String TEMP_FOLDER  = "D:/temp/esign";
    private static final String SIGNER_ID    = "signer@example.com";
    private static final String RESPONSE_URL = "https://yourapp.com/esign/callback";

    private static final String PDF_PATH     = "D:/sample.pdf";
    private static final String IMAGE_PATH   = "D:/Aadhaarlogo.jpg"; // for SignatureImage appearance
    // ─────────────────────────────────────────────────────────────────────────

    public static void main(String[] args) {
        System.out.println("=== EmudhraJarFile Test ===\n");
        try {
            testGetGatewayParameter();
            System.out.println("\n=== Test completed ===");
        } catch (Exception e) {
            System.err.println("\n=== Test failed: " + e.getMessage() + " ===");
            e.printStackTrace();
        }
    }

    /**
     * Tests getGatewayParameterMain with a real PDF (StandardSignature, PageLevel coordinates).
     */
    public static void testGetGatewayParameter() throws IOException {
        System.out.println("Test: getGatewayParameterMain");
        System.out.println("------------------------------");

        String base64Doc = readFileAsBase64(PDF_PATH);
        System.out.println("Loaded PDF: " + PDF_PATH + " (" + base64Doc.length() + " base64 chars)");

        String inputJson = buildGatewayInputJson(base64Doc);
        System.out.println("\nInput JSON (first 400 chars):");
        System.out.println(inputJson.substring(0, Math.min(400, inputJson.length())) + "...\n");

        System.out.println("Calling EmudhraJarFile.getGatewayParameterMain()...");
        String response = EmudhraJarFile.getGatewayParameterMain(inputJson);

        System.out.println("\n=== RESPONSE ===");
        if (response != null) {
            Gson gson = new GsonBuilder().setPrettyPrinting().create();
            System.out.println(gson.toJson(gson.fromJson(response, Object.class)));
        } else {
            System.out.println("Response is NULL");
        }
    }

    /**
     * Builds the gateway input JSON.
     *
     * pageLevelCoordinates format: "pageNo-x,y,width,height;pageNo-x,y,width,height"
     * e.g. "1-385,176,535,204;" means page 1, x=385, y=176, w=535, h=204
     */
    private static String buildGatewayInputJson(String base64Doc) {
        return "{"
                // ── SDK credentials ──────────────────────────────────────────
                + "\"aspID\": \"" + ASP_ID + "\","
                + "\"eSignURL\": \"" + ESIGN_URL + "\","
                + "\"eSignURLV2\": \"" + ESIGN_URL_V2 + "\","
                // ── Certificate ──────────────────────────────────────────────
                + "\"pfxPath\": \"" + PFX_PATH + "\","
                + "\"pfxPassword\": \"" + PFX_PASSWORD + "\","
                + "\"pfxAlias\": \"" + PFX_ALIAS + "\","
                // ── Session ───────────────────────────────────────────────────
                + "\"tempFolderPath\": \"" + TEMP_FOLDER + "\","
                + "\"signerID\": \"" + SIGNER_ID + "\","
                + "\"transactionID\": \"\","
                + "\"responseURL\": \"" + RESPONSE_URL + "\","
                + "\"eSignType\": \"V2\","
                + "\"authMode\": \"OTP\","
                + "\"sessionTimeout\": 10000,"
                + "\"signatureContents\": 0,"
                // ── Proxy (disabled) ─────────────────────────────────────────
                + "\"proxyReq\": false,"
                + "\"proxyIp\": \"\","
                + "\"proxyPort\": 0,"
                + "\"proxyUserID\": \"\","
                + "\"proxyUserPassword\": \"\","
                // ── Documents ─────────────────────────────────────────────────
                + "\"inputs\": ["
                + "  {"
                + "    \"base64Doc\": \"" + base64Doc + "\","
                + "    \"docURL\": \"\","
                + "    \"docInfo\": \"Sample Contract\","
                + "    \"signerName\": \"Test Signer\","
                + "    \"reason\": \"I agree to the terms\","
                + "    \"location\": \"Bangalore\","
                // pageTobeSigned=PageLevel uses pageLevelCoordinates
                + "    \"pageTobeSigned\": \"PageLevel\","
                + "    \"pageLevelCoordinates\": \"1-385,176,535,204;\","
                + "    \"appearanceType\": \"StandardSignature\","
                + "    \"coSign\": true,"
                + "    \"showAadhaarOnSignature\": false,"
                + "    \"inputType\": \"PDF\""
                + "  }"
                + "]"
                + "}";
    }

    /**
     * Quick smoke test with minimal data – expects a gateway error (bad creds)
     * but verifies JSON parsing and SDK initialisation work.
     */
    public static void testWithMinimalData() {
        System.out.println("\nTest: minimal data (expects SDK-level error)");
        System.out.println("--------------------------------------------");

        String json = "{"
                + "\"aspID\": \"TEST\","
                + "\"eSignURL\": \"https://example.com/eSignRequest\","
                + "\"eSignURLV2\": \"https://example.com/eSignPANRequest\","
                + "\"pfxPath\": \"D:/test.pfx\","
                + "\"pfxPassword\": \"test\","
                + "\"pfxAlias\": \"1\","
                + "\"tempFolderPath\": \"D:/temp\","
                + "\"signerID\": \"test@example.com\","
                + "\"responseURL\": \"https://example.com/callback\","
                + "\"eSignType\": \"V2\","
                + "\"authMode\": \"OTP\","
                + "\"inputs\": [{"
                + "  \"base64Doc\": \"JVBER\","
                + "  \"docInfo\": \"Test\","
                + "  \"pageTobeSigned\": \"Last\","
                + "  \"appearanceType\": \"StandardSignature\","
                + "  \"coordinates\": \"BottomRight\""
                + "}]"
                + "}";

        System.out.println("Response: " + EmudhraJarFile.getGatewayParameterMain(json));
    }

    private static String readFileAsBase64(String filePath) throws IOException {
        Path path = Paths.get(filePath);
        if (!Files.exists(path)) {
            throw new IOException("File not found: " + filePath);
        }
        return Base64.getEncoder().encodeToString(Files.readAllBytes(path));
    }
}
