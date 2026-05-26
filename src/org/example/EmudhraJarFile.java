package org.example;

import com.emudhra.esign.ReturnDocument;
import com.emudhra.esign.eSign;
import com.emudhra.esign.eSignInput;
import com.emudhra.esign.eSignInputBuilder;
import com.emudhra.esign.eSignServiceReturn;
import com.emudhra.esign.eSignSettings;
import com.google.gson.Gson;
import com.google.gson.annotations.SerializedName;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.List;

/**
 * JSON-over-CLI bridge so Node.js (and other non-JVM runtimes) can call the
 * eMudhra eSign SDK.  Every public method accepts a JSON string and returns a
 * JSON string – it never throws to the caller.
 *
 * Underlying SDK: com.emudhra.esign (eSignASPLibrary5_10.jar)
 */
public class EmudhraJarFile {

    public EmudhraJarFile() {
    }

    public static void main(String[] args) {
    }

    // ── Phase 1: initiate signing ─────────────────────────────────────────────

    /**
     * Builds and sends the eSign gateway request.
     *
     * @param inputJson JSON string matching {@link GetGatewayParamsInput}
     * @return JSON-serialised {@code eSignServiceReturn}; on error returns a
     *         JSON object with {@code status:0}, {@code errorCode}, {@code errorMessage}.
     */
    public static String getGatewayParameterMain(String inputJson) {
        Gson gson = new Gson();
        try {
            GetGatewayParamsInput p = gson.fromJson(inputJson, GetGatewayParamsInput.class);

            eSign eSignObj = new eSign(
                    p.getAspID(),
                    p.getESignURL(),
                    p.getESignURLV2(),
                    p.getPfxPath(),
                    p.getPfxPassword(),
                    p.getPfxAlias(),
                    p.isProxyReq(),
                    p.getProxyIp(),
                    p.getProxyPort(),
                    p.getSessionTimeout(),
                    eSignSettings.LogType.AllLog,
                    p.getProxyUserID(),
                    p.getProxyUserPassword(),
                    null,                       // pdfViewerLicence – not used
                    p.getSignatureContents()
            );

            List<eSignInput> inputsList = new ArrayList<>();
            for (InputData doc : p.getInputs()) {
                inputsList.add(buildInput(doc));
            }

            eSignServiceReturn result = eSignObj.getGatewayParameter(
                    new ArrayList<>(inputsList),
                    p.getSignerID(),
                    p.getTransactionID() != null ? p.getTransactionID() : "",
                    p.getResponseURL(),
                    p.getRedirectUrl(),
                    p.getTempFolderPath(),
                    p.getESignAPIVersion(),
                    p.getAuthMode()
            );

            return gson.toJson(result);

        } catch (NoSuchAlgorithmException e) {
            System.err.println("Crypto error in getGatewayParameter: " + e.getMessage());
            e.printStackTrace(System.err);
            return errorJson(gson, "CRYPTO_ERROR", e.getMessage());
        } catch (Exception e) {
            System.err.println("Error in getGatewayParameter: " + e.getMessage());
            e.printStackTrace(System.err);
            return errorJson(gson, "ERROR", e.getMessage());
        }
    }

    // ── Phase 2: retrieve signed document ────────────────────────────────────

    /**
     * Injects the gateway-returned PKCS7 signature back into the PDF.
     *
     * @param inputJson JSON string matching {@link CompleteSigningJsonData}
     * @return JSON-serialised {@code eSignServiceReturn}.  When
     *         {@code signedFilePath} is provided the signed PDFs are also
     *         written to {@code <signedFilePath>0.pdf}, {@code <signedFilePath>1.pdf}, …
     */
    public static String getSignedDocMain(String inputJson) {
        Gson gson = new Gson();
        try {
            CompleteSigningJsonData p = gson.fromJson(inputJson, CompleteSigningJsonData.class);

            eSign eSignObj = new eSign(
                    p.getAspID(),
                    p.getESignURL(),
                    p.getESignURLV2(),
                    p.getPfxPath(),
                    p.getPfxPassword(),
                    p.getPfxAlias(),
                    p.isProxyReq(),
                    p.getProxyIp(),
                    p.getProxyPort(),
                    p.getSessionTimeout(),
                    eSignSettings.LogType.AllLog,
                    p.getProxyUserID(),
                    p.getProxyUserPassword(),
                    null,
                    p.getSignatureContents()
            );

            eSignServiceReturn result = eSignObj.getSigedDocument(
                    p.getResponseXML(),
                    p.getPreSignedTempFile()
            );

            // Optionally persist signed PDFs to disk
            if (result.getStatus() == 1
                    && p.getSignedFilePath() != null
                    && !p.getSignedFilePath().isEmpty()) {
                ArrayList<ReturnDocument> docs = result.getReturnDocuments();
                if (docs != null) {
                    for (int i = 0; i < docs.size(); i++) {
                        ReturnDocument doc = docs.get(i);
                        if (doc.getStatus() == 1
                                && doc.getSignedDocument() != null
                                && !doc.getSignedDocument().isEmpty()) {
                            byte[] bytes = esign.text.pdf.codec.Base64.decode(doc.getSignedDocument());
                            Files.write(Paths.get(p.getSignedFilePath() + i + ".pdf"), bytes);
                        }
                    }
                }
            }

            return gson.toJson(result);

        } catch (NoSuchAlgorithmException e) {
            System.err.println("Crypto error in getSignedDocument: " + e.getMessage());
            e.printStackTrace(System.err);
            return errorJson(gson, "CRYPTO_ERROR", e.getMessage());
        } catch (IOException e) {
            System.err.println("IO error writing signed file: " + e.getMessage());
            e.printStackTrace(System.err);
            return errorJson(gson, "IO_ERROR", e.getMessage());
        } catch (Exception e) {
            System.err.println("Error in getSignedDocument: " + e.getMessage());
            e.printStackTrace(System.err);
            return errorJson(gson, "ERROR", e.getMessage());
        }
    }

    // ── Builder helper ────────────────────────────────────────────────────────

    private static eSignInput buildInput(InputData d) {
        eSignInputBuilder b = eSignInputBuilder.init()
                .setDocBase64(nvl(d.getBase64doc()))
                .setDocHash(nvl(d.getDocHash()))
                .setDocInfo(nvl(d.getDocInfo()))
                .setDocURL(nvl(d.getDocURL()))
                .setSignedBy(nvl(d.getSignerName()))
                .setReason(nvl(d.getReason()))
                .setLocation(nvl(d.getLocation()))
                .setCoSign(d.isCoSign())
                .setInputType(d.getInputType())
                .setShowAadhaarOnSignature(d.isShowAadhaarOnSignature())
                .isRightOrigin(false);

        if (d.getAppearanceText() != null && !d.getAppearanceText().isEmpty()) {
            b.setAppearanceText(d.getAppearanceText());
        }
        if (d.getSignatureFontSize() > 0) {
            b.setSignatureFontSize(d.getSignatureFontSize());
        }

        eSign.AppearanceType at = d.getAppearanceType();
        b.setAppearanceType(at);
        if (at == eSign.AppearanceType.SignatureImage && d.getImageSignBase64() != null) {
            b.setSignatureImage(d.getImageSignBase64());
        } else if (at == eSign.AppearanceType.OneLiner && d.getOneLiner() != null) {
            b.setOneLiner(d.getOneLiner());
        }

        eSign.PageTobeSigned pts = d.getPageTobeSigned();
        b.setPageTobeSigned(pts);
        if (pts == eSign.PageTobeSigned.PageLevel) {
            b.setPageLevelCoordinates(nvl(d.getPageLevelCoordinates()));
        } else if (pts == eSign.PageTobeSigned.Specify) {
            b.setPageNumbers(nvl(d.getPageNumbers()));
            if (d.getCoordinates() != null) {
                b.setCoordinates(d.getCoordinates());
            }
        } else {
            if (d.getCoordinates() != null) {
                b.setCoordinates(d.getCoordinates());
            }
        }

        return b.build();
    }

    private static String nvl(String s) {
        return s != null ? s : "";
    }

    private static String errorJson(Gson gson, String code, String message) {
        return gson.toJson(new ErrorResponse(code, message != null ? message : "Unknown error"));
    }

    // ── Input DTOs ────────────────────────────────────────────────────────────

    /**
     * JSON input for {@link #getGatewayParameterMain}.
     *
     * Required fields:
     *   aspID, eSignURL, eSignURLV2, pfxPath, pfxPassword, pfxAlias,
     *   tempFolderPath, signerID, responseURL, eSignType, inputs[]
     *
     * Optional:
     *   transactionID, redirectUrl, authMode (default OTP),
     *   proxyReq/proxyIp/proxyPort/proxyUserID/proxyUserPassword,
     *   sessionTimeout, signatureContents
     */
    static class GetGatewayParamsInput {

        private String aspID;
        private String eSignURL;
        private String eSignURLV2;
        private String pfxPath;
        private String pfxPassword;
        private String pfxAlias;
        private String tempFolderPath;
        private String signerID;
        private String transactionID;
        private String responseURL;
        /** Falls back to responseURL when absent. */
        private String redirectUrl;
        /** "V2" (Aadhaar) or "V3" (PAN). Defaults to V2. */
        private String eSignType;
        /** "OTP" | "FingerPrint" | "IRIS" | "FaceRecognition" or 1-4. Defaults to OTP. */
        private String authMode;
        private boolean proxyReq;
        private String proxyIp;
        private int proxyPort;
        private int sessionTimeout;
        private String proxyUserID;
        private String proxyUserPassword;
        private int signatureContents;
        private List<InputData> inputs;

        public String getAspID()              { return aspID; }
        public String getESignURL()           { return eSignURL; }
        public String getESignURLV2()         { return eSignURLV2; }
        public String getPfxPath()            { return pfxPath; }
        public String getPfxPassword()        { return pfxPassword; }
        public String getPfxAlias()           { return pfxAlias; }
        public String getTempFolderPath()     { return tempFolderPath; }
        public String getSignerID()           { return signerID; }
        public String getTransactionID()      { return transactionID; }
        public String getResponseURL()        { return responseURL; }
        public boolean isProxyReq()           { return proxyReq; }
        public String getProxyIp()            { return proxyIp != null ? proxyIp : ""; }
        public int getProxyPort()             { return proxyPort; }
        public int getSessionTimeout()        { return sessionTimeout; }
        public String getProxyUserID()        { return proxyUserID; }
        public String getProxyUserPassword()  { return proxyUserPassword; }
        public int getSignatureContents()     { return signatureContents; }
        public List<InputData> getInputs()    { return inputs; }

        /** Returns redirectUrl if set, otherwise falls back to responseURL. */
        public String getRedirectUrl() {
            return (redirectUrl != null && !redirectUrl.isEmpty()) ? redirectUrl : responseURL;
        }

        public eSign.eSignAPIVersion getESignAPIVersion() {
            return "V3".equalsIgnoreCase(eSignType)
                    ? eSign.eSignAPIVersion.V3
                    : eSign.eSignAPIVersion.V2;
        }

        public eSign.AuthMode getAuthMode() {
            if (authMode == null || authMode.trim().isEmpty()) {
                return eSign.AuthMode.OTP;
            }
            String mode = authMode.trim();
            // Numeric shorthand
            try {
                switch (Integer.parseInt(mode)) {
                    case 1: return eSign.AuthMode.OTP;
                    case 2: return eSign.AuthMode.FingerPrint;
                    case 3: return eSign.AuthMode.IRIS;
                    case 4: return eSign.AuthMode.FaceRecognition;
                    default:
                        System.err.println("Warning: invalid authMode number '" + mode + "', defaulting to OTP");
                        return eSign.AuthMode.OTP;
                }
            } catch (NumberFormatException ignored) { /* fall through to string match */ }

            switch (mode.toUpperCase()) {
                case "OTP":             return eSign.AuthMode.OTP;
                case "FINGERPRINT":     return eSign.AuthMode.FingerPrint;
                case "IRIS":            return eSign.AuthMode.IRIS;
                case "FACERECOGNITION":
                case "FACE":            return eSign.AuthMode.FaceRecognition;
                default:
                    System.err.println("Warning: unknown authMode '" + mode + "', defaulting to OTP");
                    return eSign.AuthMode.OTP;
            }
        }
    }

    /**
     * Per-document configuration inside the inputs[] array.
     *
     * Supply either base64Doc (inline PDF) or docURL (remote PDF), not both.
     * For HASH mode, supply docHash and set inputType to "HASH".
     *
     * Enums are deserialized by Gson using enum name (case-sensitive):
     *   appearanceType : StandardSignature | SignatureImage | OneLiner |
     *                    advanceSignature | ColoredGraphic | BackgroundImage
     *   pageTobeSigned : All | Even | Odd | Last | First | PageLevel | Specify
     *   coordinates    : TopLeft | TopMiddle | TopRight | CenterLeft |
     *                    CenterMiddle | CenterRight | BottomLeft |
     *                    BottomMiddle | BottomRight
     *   inputType      : PDF | HASH
     */
    static class InputData {

        @SerializedName(value = "base64Doc", alternate = {"base64doc"})
        private String base64doc;
        private String docHash;
        private String docInfo;
        private String docURL;
        private String signerName;
        private String reason;
        private String location;
        /**
         * Page-level coordinates string, e.g. "1-100,200,150,50;2-300,400,150,50".
         * Also accepted as "pageCoordinates" for backward compatibility.
         */
        @SerializedName(value = "pageLevelCoordinates", alternate = {"pageCoordinates"})
        private String pageLevelCoordinates;
        /** Comma-separated page numbers when pageTobeSigned is Specify, e.g. "1,3,5". */
        private String pageNumbers;
        private boolean coSign;
        private String appearanceText;
        private int signatureFontSize;
        /** Base64 image for SignatureImage appearance. */
        private String imageSignBase64;
        /** Text for OneLiner appearance. */
        private String oneLiner;
        private boolean showAadhaarOnSignature;
        /** Defaults to StandardSignature if absent. */
        private eSign.AppearanceType appearanceType;
        /** Defaults to Last if absent. */
        private eSign.PageTobeSigned pageTobeSigned;
        /** Preset quadrant position; ignored when using pageLevelCoordinates. */
        private eSign.Coordinates coordinates;
        /** Defaults to PDF if absent. */
        private eSign.InputType inputType;

        public String getBase64doc()            { return base64doc; }
        public String getDocHash()              { return docHash; }
        public String getDocInfo()              { return docInfo; }
        public String getDocURL()               { return docURL; }
        public String getSignerName()           { return signerName; }
        public String getReason()               { return reason; }
        public String getLocation()             { return location; }
        public String getPageLevelCoordinates() { return pageLevelCoordinates; }
        public String getPageNumbers()          { return pageNumbers; }
        public boolean isCoSign()               { return coSign; }
        public String getAppearanceText()       { return appearanceText; }
        public int getSignatureFontSize()       { return signatureFontSize; }
        public String getImageSignBase64()      { return imageSignBase64; }
        public String getOneLiner()             { return oneLiner; }
        public boolean isShowAadhaarOnSignature() { return showAadhaarOnSignature; }
        public eSign.Coordinates getCoordinates() { return coordinates; }

        public eSign.AppearanceType getAppearanceType() {
            return appearanceType != null ? appearanceType : eSign.AppearanceType.StandardSignature;
        }

        public eSign.PageTobeSigned getPageTobeSigned() {
            return pageTobeSigned != null ? pageTobeSigned : eSign.PageTobeSigned.Last;
        }

        public eSign.InputType getInputType() {
            return inputType != null ? inputType : eSign.InputType.PDF;
        }
    }

    /**
     * JSON input for {@link #getSignedDocMain}.
     *
     * Required: aspID, eSignURL, eSignURLV2, pfxPath, pfxPassword, pfxAlias,
     *           responseXML, preSignedTempFile
     * Optional: signedFilePath (write PDFs to disk), proxyReq/… , signatureContents
     */
    static class CompleteSigningJsonData {

        private String aspID;
        private String eSignURL;
        private String eSignURLV2;
        private String pfxPath;
        private String pfxPassword;
        private String pfxAlias;
        private String responseXML;
        private String preSignedTempFile;
        private boolean proxyReq;
        private String proxyIp;
        private int proxyPort;
        private int sessionTimeout;
        private String proxyUserID;
        private String proxyUserPassword;
        /**
         * Optional base path for writing signed PDFs.
         * Files are written as {@code <signedFilePath>0.pdf}, {@code <signedFilePath>1.pdf}, …
         * Leave empty/null to skip file writing; the signed data is still in the JSON response.
         */
        private String signedFilePath;
        private int signatureContents;

        public String getAspID()              { return aspID; }
        public String getESignURL()           { return eSignURL; }
        public String getESignURLV2()         { return eSignURLV2; }
        public String getPfxPath()            { return pfxPath; }
        public String getPfxPassword()        { return pfxPassword; }
        public String getPfxAlias()           { return pfxAlias; }
        public String getResponseXML()        { return responseXML; }
        public String getPreSignedTempFile()  { return preSignedTempFile; }
        public boolean isProxyReq()           { return proxyReq; }
        public String getProxyIp()            { return proxyIp != null ? proxyIp : ""; }
        public int getProxyPort()             { return proxyPort; }
        public int getSessionTimeout()        { return sessionTimeout; }
        public String getProxyUserID()        { return proxyUserID; }
        public String getProxyUserPassword()  { return proxyUserPassword; }
        public String getSignedFilePath()     { return signedFilePath; }
        public int getSignatureContents()     { return signatureContents; }
    }

    /** Returned on any exception so the caller always gets valid JSON. */
    static class ErrorResponse {
        private final int status = 0;
        private final String errorCode;
        private final String errorMessage;

        ErrorResponse(String errorCode, String errorMessage) {
            this.errorCode = errorCode;
            this.errorMessage = errorMessage;
        }
    }
}
