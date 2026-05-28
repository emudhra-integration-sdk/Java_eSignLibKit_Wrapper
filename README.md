# eMudhra eSign Node.js Bridge

> A thin JSON-over-CLI bridge that makes the [eMudhra eSign Java SDK](https://github.com/emudhraltd/java-esign-sdk) callable from Node.js — or any non-JVM runtime.

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Java](https://img.shields.io/badge/Java-8%2B-orange.svg)](https://adoptium.net)
[![Node.js](https://img.shields.io/badge/Node.js-12%2B-green.svg)](https://nodejs.org)

---

## Table of Contents

- [Why this exists](#why-this-exists)
- [How it works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
  - [1. Clone and get dependencies](#1-clone-and-get-dependencies)
  - [2. Build the SDK](#2-build-the-sdk)
  - [3. Configure local.properties](#3-configure-localproperties)
  - [4. Build the bridge JAR](#4-build-the-bridge-jar)
- [Node.js Integration](#nodejs-integration)
  - [Installation](#installation)
  - [Phase 1 — Initiate signing](#phase-1--initiate-signing)
  - [Phase 2 — Retrieve signed document](#phase-2--retrieve-signed-document)
  - [Full workflow example](#full-workflow-example)
- [Python Integration](#python-integration)
- [CLI Usage](#cli-usage)
- [API Reference](#api-reference)
  - [getGatewayParameter](#getgatewayparameter)
  - [getSignedDocument](#getsigneddocument)
  - [Enum values](#enum-values)
  - [Response format](#response-format)
  - [Error responses](#error-responses)
- [Building from Source](#building-from-source)
- [Contributing](#contributing)
- [License](#license)

---

## Why this exists

Node.js cannot call Java methods directly. The eMudhra eSign SDK is a Java library (`com.emudhra.esign`). This bridge solves that by:

1. Accepting a JSON payload on the command line
2. Deserializing it and calling the appropriate SDK method
3. Serializing the response to JSON on stdout

Your Node.js code spawns the JAR as a child process and communicates entirely through JSON.

---

## How it works

```
┌──────────────────────────────────────────────────────────────────┐
│  Your Node.js app                                                │
│                                                                  │
│   const result = await client.getGatewayParameter({ ... });     │
└───────────────────────┬──────────────────────────────────────────┘
                        │  child_process.spawn()
                        │  args: ['getGatewayParameter', '{"aspID":...}']
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│  newJarEmudhra.jar  (this project)                               │
│                                                                  │
│   NodeJSBridge.main()                                            │
│     └─► EmudhraJarFile.getGatewayParameterMain(jsonString)       │
│           └─► eSignInputBuilder  (parse JSON → SDK objects)      │
│           └─► eSign.getGatewayParameter(...)  ──────────────┐    │
└─────────────────────────────────────────────────────────────┼────┘
                                                              │
┌─────────────────────────────────────────────────────────────┼────┐
│  eSignASPLibrary (eMudhra eSign SDK)                         │   │
│                                                              ▼   │
│   1. SHA-256 hash the PDF (never sends full PDF)                 │
│   2. Build & sign XML request with ASP certificate              │
│   3. POST to eMudhra gateway → receive gatewayParameter         │
└──────────────────────────────────────────────────────────────────┘
                        │
                        │  stdout: {"status":1,"gatewayParameter":"..."}
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│  Your Node.js app                                                │
│   → redirect user to gateway with gatewayParameter              │
│   → after signing, call getSignedDocument() for Phase 2         │
└──────────────────────────────────────────────────────────────────┘
```

The bridge never throws to the caller — all errors are returned as structured JSON.

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Java | 8+ | Must be on `PATH` (`java -version`) |
| Apache Ant | 1.9+ | Only needed to build from source |
| Node.js | 12+ | To use the Node.js client |
| eMudhra eSign SDK | 5.5+ | See [Build the SDK](#2-build-the-sdk) |
| ASP ID & gateway URLs | — | Obtained from eMudhra |
| PFX certificate | — | Issued by eMudhra for your ASP |

---

## Setup

### 1. Clone and get dependencies

```bash
git clone https://github.com/emudhraltd/esign-node-bridge.git
cd esign-node-bridge

# Download open-source dependency JARs into lib/
# Windows:
.\scripts\download-deps.ps1

# Linux / macOS:
bash scripts/download-deps.sh
```

### 2. Build the SDK

This bridge wraps the eMudhra eSign SDK. Clone and build it:

```bash
git clone https://github.com/emudhraltd/java-esign-sdk.git
cd java-esign-sdk
ant clean jar
# Output: dist/eSignASPLibrary5_5.jar
```

### 3. Configure local.properties

```bash
cp local.properties.example local.properties
```

Edit `local.properties` and set the path to the SDK JAR you just built:

```properties
file.reference.eSignASPLibrary5_10.jar=../java-esign-sdk/dist/eSignASPLibrary5_5.jar
```

All other entries default to `lib/*.jar` (populated by the download script).

### 4. Build the bridge JAR

```bash
ant clean jar
# Output: dist/newJarEmudhra.jar  (~12 MB fat JAR)
```

> **Windows note:** If `ant` is not on your PATH, use the NetBeans bundled version:
> ```powershell
> & "C:\Program Files\NetBeans-19\netbeans\extide\ant\bin\ant.bat" clean jar
> ```

---

## Node.js Integration

### Installation

Copy (or symlink) `nodejs-esign-client/esign-client.js` into your project, or
reference it with a relative `require()`:

```javascript
const ESignClient = require('./nodejs-esign-client/esign-client');
const client = new ESignClient('/absolute/path/to/dist/newJarEmudhra.jar');
```

### Phase 1 — Initiate signing

```javascript
const fs = require('fs');

const pdfBase64 = fs.readFileSync('/path/to/document.pdf').toString('base64');

const result = await client.getGatewayParameter({
    // ── SDK identity ──────────────────────────────────────────────
    aspID:      'YOUR_ASP_ID',
    eSignURL:   'https://esign-uat.emudhra.com/eSignRequest',    // V2 Aadhaar
    eSignURLV2: 'https://esign-uat.emudhra.com/eSignPANRequest', // V3 PAN

    // ── ASP certificate ───────────────────────────────────────────
    pfxPath:     '/certs/asp-cert.pfx',
    pfxPassword: 'secret',
    pfxAlias:    '1',

    // ── Session ───────────────────────────────────────────────────
    tempFolderPath: '/tmp/esign',
    signerID:       'user@example.com',
    responseURL:    'https://yourapp.com/esign/callback',
    eSignType:      'V2',    // 'V2' (Aadhaar) | 'V3' (PAN)
    authMode:       'OTP',   // 'OTP' | 'FingerPrint' | 'IRIS' | 'FaceRecognition'

    // ── Documents ─────────────────────────────────────────────────
    inputs: [
        {
            base64Doc:    pdfBase64,
            docInfo:      'Loan Agreement',
            signerName:   'Jane Smith',
            reason:       'I agree to the terms',
            location:     'Bangalore',
            coSign:       true,
            inputType:    'PDF',

            // Signature placement
            pageTobeSigned:       'PageLevel',
            pageLevelCoordinates: '1-400,100,150,50;', // page-x,y,width,height
            appearanceType:       'StandardSignature'
        }
    ]
});

if (result.status === 1) {
    // Redirect user to gateway
    const gatewayUrl = `https://esign-uat.emudhra.com/esign?eSignRequest=${result.gatewayParameter}`;
    // Store for Phase 2:
    const preSignedTempFile = result.preSignedTempFile;
    const transactionID     = result.transactionID;
} else {
    console.error('Phase 1 failed:', result.errorCode, result.errorMessage);
}
```

### Phase 2 — Retrieve signed document

Call this from your callback URL handler after the user signs at the gateway:

```javascript
// req.body contains the XML posted by the eMudhra gateway
const result = await client.getSignedDocument({
    aspID:         'YOUR_ASP_ID',
    eSignURL:      'https://esign-uat.emudhra.com/eSignRequest',
    eSignURLV2:    'https://esign-uat.emudhra.com/eSignPANRequest',
    pfxPath:       '/certs/asp-cert.pfx',
    pfxPassword:   'secret',
    pfxAlias:      '1',

    responseXML:      req.body,          // XML from gateway callback
    preSignedTempFile: session.preSignedTempFile,  // from Phase 1

    // Optional: write signed PDFs to disk
    // Produces: /output/signed-0.pdf, /output/signed-1.pdf, …
    signedFilePath: '/output/signed-'
});

if (result.status === 1) {
    result.returnDocuments.forEach((doc, i) => {
        if (doc.status === 1) {
            // doc.signedDocument — base64-encoded signed PDF
            const pdfBuffer = Buffer.from(doc.signedDocument, 'base64');
            fs.writeFileSync(`/output/signed-${i}.pdf`, pdfBuffer);
        }
    });
} else {
    console.error('Phase 2 failed:', result.errorCode, result.errorMessage);
}
```

### Full workflow example

See [`nodejs-esign-client/index.js`](nodejs-esign-client/index.js) for a
self-contained example of the complete two-phase flow.

---

## CLI Usage

The JAR can be called directly — useful for testing or integrating with
non-Node.js runtimes:

```bash
java -cp dist/newJarEmudhra.jar org.example.NodeJSBridge \
    getGatewayParameter \
    '{"aspID":"...","eSignURL":"...","inputs":[...]}'
```

```bash
java -cp dist/newJarEmudhra.jar org.example.NodeJSBridge \
    getSignedDocument \
    '{"aspID":"...","responseXML":"...","preSignedTempFile":"..."}'
```

stdout → JSON result &nbsp;&nbsp; stderr → diagnostic messages (never affects the JSON)

---

## API Reference

### `getGatewayParameter`

**Java method:** `EmudhraJarFile.getGatewayParameterMain(String inputJson)`  
**SDK method:** `eSign.getGatewayParameter(...)`

#### Input JSON

```jsonc
{
    // ── Identity (required) ──────────────────────────────────────────────────
    "aspID":      "YOUR_ASP_ID",          // eMudhra ASP ID
    "eSignURL":   "https://...",          // V2 (Aadhaar) gateway URL
    "eSignURLV2": "https://...",          // V3 (PAN) gateway URL

    // ── ASP Certificate (required) ───────────────────────────────────────────
    "pfxPath":     "/path/to/cert.pfx",
    "pfxPassword": "password",
    "pfxAlias":    "1",

    // ── Session (required) ───────────────────────────────────────────────────
    "tempFolderPath": "/tmp/esign",       // writable scratch directory
    "signerID":       "user@example.com", // signer email or ID
    "responseURL":    "https://yourapp.com/callback",
    "transactionID":  "",                 // optional; SDK generates one if blank
    "redirectUrl":    "",                 // optional; falls back to responseURL

    // ── API & auth (optional, defaults shown) ────────────────────────────────
    "eSignType": "V2",    // "V2" (Aadhaar) | "V3" (PAN)
    "authMode":  "OTP",   // "OTP" | "FingerPrint" | "IRIS" | "FaceRecognition"
                          //   or numeric: 1 | 2 | 3 | 4

    // ── Proxy (optional) ─────────────────────────────────────────────────────
    "proxyReq":          false,
    "proxyIp":           "",
    "proxyPort":         0,
    "proxyUserID":       "",
    "proxyUserPassword": "",

    // ── Misc (optional) ──────────────────────────────────────────────────────
    "sessionTimeout":   0,    // ms; 0 = SDK default
    "signatureContents": 0,   // reserved; use 0

    // ── Documents (required, 1–5 items) ──────────────────────────────────────
    "inputs": [
        {
            // Document source — provide one of:
            "base64Doc": "<base64-encoded PDF>",  // also accepted as "base64doc"
            "docURL":    "",                      // remote URL (instead of base64)

            // For HASH mode:
            "docHash":   "",                      // pre-computed SHA-256 hex
            "inputType": "PDF",                   // "PDF" | "HASH"

            // Signer info (optional but recommended)
            "docInfo":    "Loan Agreement",
            "signerName": "Jane Smith",
            "reason":     "I agree",
            "location":   "Bangalore",
            "coSign":     true,

            // Appearance
            "appearanceType":    "StandardSignature",
            "imageSignBase64":   "",   // base64 image for SignatureImage type
            "oneLiner":          "",   // text for OneLiner type
            "appearanceText":    "",   // custom text overlay
            "signatureFontSize": 0,
            "showAadhaarOnSignature": false,

            // Page & position
            "pageTobeSigned":       "Last",
            "pageLevelCoordinates": "1-400,100,150,50;",
            "pageNumbers":          "1,3,5",
            "coordinates":          "BottomRight"
        }
    ]
}
```

#### Response (on success)

```jsonc
{
    "status":           1,                   // 1 = success, 0 = failure
    "transactionID":    "TXN-2024-001",
    "preSignedTempFile": "/tmp/esign/TXN-2024-001.tmp",
    "gatewayParameter": "<base64-encoded eSign request>",
    "responseCode":     "1",
    "requestXML":       "<xml>...",
    "returnDocuments":  null                 // null in Phase 1
}
```

---

### `getSignedDocument`

**Java method:** `EmudhraJarFile.getSignedDocMain(String inputJson)`  
**SDK method:** `eSign.getSigedDocument(...)`

#### Input JSON

```jsonc
{
    // ── Identity & certificate (same as Phase 1) ──────────────────────────────
    "aspID":      "YOUR_ASP_ID",
    "eSignURL":   "https://...",
    "eSignURLV2": "https://...",
    "pfxPath":    "/path/to/cert.pfx",
    "pfxPassword": "password",
    "pfxAlias":   "1",

    // ── Signing response (required) ───────────────────────────────────────────
    "responseXML":      "<xml posted by gateway to your callback URL>",
    "preSignedTempFile": "/tmp/esign/TXN-2024-001.tmp",

    // ── Output (optional) ────────────────────────────────────────────────────
    // If set, signed PDFs are written as <signedFilePath>0.pdf, <signedFilePath>1.pdf, …
    // If omitted, signed data is only in the JSON response (returnDocuments[].signedDocument).
    "signedFilePath": "/output/signed-",

    // ── Proxy (optional) ─────────────────────────────────────────────────────
    "proxyReq": false, "proxyIp": "", "proxyPort": 0,
    "proxyUserID": "", "proxyUserPassword": "",
    "sessionTimeout": 0, "signatureContents": 0
}
```

#### Response (on success)

```jsonc
{
    "status":      1,
    "transactionID": "TXN-2024-001",
    "responseXML": "<signed xml from gateway>",
    "returnDocuments": [
        {
            "status":         1,
            "docId":          0,
            "docInfo":        "Loan Agreement",
            "signedDocument": "<base64-encoded signed PDF>",
            "documentHash":   "<SHA-256 hash>",
            "inputType":      "PDF"
        }
    ]
}
```

---

### Enum values

| Field | Accepted values |
|-------|----------------|
| `eSignType` | `V2` (Aadhaar), `V3` (PAN) |
| `authMode` | `OTP`, `FingerPrint`, `IRIS`, `FaceRecognition` · or `1`, `2`, `3`, `4` |
| `appearanceType` | `StandardSignature` `SignatureImage` `OneLiner` `advanceSignature` `ColoredGraphic` `BackgroundImage` |
| `pageTobeSigned` | `All` `Even` `Odd` `Last` `First` `PageLevel` `Specify` |
| `coordinates` | `TopLeft` `TopMiddle` `TopRight` `CenterLeft` `CenterMiddle` `CenterRight` `BottomLeft` `BottomMiddle` `BottomRight` |
| `inputType` | `PDF`, `HASH` |

> **`pageLevelCoordinates` format:** `"pageNo-x,y,width,height;"` per page, e.g.
> `"1-385,176,535,204;"` means page 1 at x=385, y=176, w=535, h=204 (PDF points).
> Separate multiple pages with `;`.

> **Enum names are case-sensitive** (Gson default). `authMode` alone accepts both
> numeric and string forms.

---

### Response format

All responses from both methods share this top-level structure:

| Field | Type | Description |
|-------|------|-------------|
| `status` | `int` | `1` = success, `0` = failure |
| `transactionID` | `string` | Transaction identifier |
| `gatewayParameter` | `string` | *(Phase 1 only)* Base64 eSign request to post to gateway |
| `preSignedTempFile` | `string` | *(Phase 1 only)* Temp file path — store and pass to Phase 2 |
| `responseCode` | `string` | Gateway response code |
| `errorCode` | `string` | Error code when `status=0` |
| `errorMessage` | `string` | Human-readable error when `status=0` |
| `returnDocuments` | `array` | *(Phase 2 only)* Signed document objects |
| `returnDocuments[].signedDocument` | `string` | Base64-encoded signed PDF |
| `returnDocuments[].status` | `int` | Per-document status (`1`=ok, `0`=failed) |

---

### Error responses

Any exception (bad credentials, network failure, invalid input) is caught and
returned as structured JSON — the process always exits 0 and stdout is always
valid JSON:

```json
{
    "status": 0,
    "errorCode": "ERROR",
    "errorMessage": "Descriptive message here"
}
```

`errorCode` values: `CRYPTO_ERROR`, `IO_ERROR`, `ERROR`.
Diagnostic stack traces are written to **stderr** so stdout stays clean JSON.

---

## Building from Source

### Project structure

```
esign-node-bridge/
├── src/org/example/
│   ├── EmudhraJarFile.java       Core bridge — JSON → SDK → JSON
│   ├── NodeJSBridge.java         CLI entry point (main)
│   └── EmudhraJarFileTest.java   Manual test harness
├── nodejs-esign-client/
│   ├── esign-client.js           Node.js client class
│   ├── index.js                  Full workflow example
│   └── package.json
├── scripts/
│   ├── download-deps.ps1         Download open-source JARs (Windows)
│   └── download-deps.sh          Download open-source JARs (Linux/macOS)
├── lib/                          Open-source dependency JARs (gitignored)
│   └── README.md
├── build.xml                     Ant build (imports local.properties)
├── local.properties.example      Template for local paths
├── nbproject/project.properties  Build configuration
├── CONTRIBUTING.md               Contribution guidelines (also in root)
├── CONTRIBUTING.md
└── LICENSE
```

### Build commands

```bash
# Full clean + build → dist/newJarEmudhra.jar
ant clean jar

# Incremental build
ant jar

# Run the Java test harness (update constants at top of EmudhraJarFileTest.java first)
javac -cp dist/newJarEmudhra.jar src/org/example/EmudhraJarFileTest.java -d build/classes
java  -cp "dist/newJarEmudhra.jar;build/classes" org.example.EmudhraJarFileTest
```

### How the fat JAR is assembled

The Ant `-post-jar` target:
1. Creates a temp directory
2. Unpacks all dependency JARs (SDK + open-source libs) into it, stripping signature files
3. Merges compiled bridge classes with unpacked dependencies
4. Repacks everything into `dist/newJarEmudhra.jar`

This produces a single self-contained JAR that requires only Java on the target machine.

---

## Python Integration

A single-file Python wrapper is included in [`python-esign-client/`](python-esign-client/).  
It mirrors the Node.js client — no web framework required, pure standard library.

```python
from esign_client import ESignClient

client = ESignClient('/path/to/newJarEmudhra.jar')

result = client.get_gateway_parameter({ 'aspID': '...', 'inputs': [...], ... })
result = client.get_signed_document({ 'responseXML': '...', 'preSignedTempFile': '...', ... })
```

See **[python-esign-client/README.md](python-esign-client/README.md)** for the full usage guide.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

The **source code** of this bridge is licensed under the [Apache License 2.0](LICENSE).

The **compiled fat JAR** (`dist/newJarEmudhra.jar`) bundles the eMudhra eSign SDK,
which embeds [iText](https://itextpdf.com/) (AGPL-3.0). Distributing the fat JAR
therefore requires compliance with AGPL-3.0. See the [LICENSE](LICENSE) file for
full third-party notices.
