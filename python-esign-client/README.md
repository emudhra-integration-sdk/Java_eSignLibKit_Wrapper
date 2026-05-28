# eMudhra eSign — Python Integration

A single-file Python wrapper that lets any Python 3.6+ application call the
eMudhra eSign bridge JAR via subprocess. No web framework required.

---

## How it works

```
Your Python app
      │
      │  client.get_gateway_parameter({...})
      ▼
subprocess: java -cp newJarEmudhra.jar NodeJSBridge getGatewayParameter '{"aspID":...}'
      │
      ◄── JSON: {status:1, gatewayParameter, preSignedTempFile, transactionID, ...}
      │
      │  client.get_signed_document({...})
      ▼
subprocess: java -cp newJarEmudhra.jar NodeJSBridge getSignedDocument '{"responseXML":...}'
      │
      ◄── JSON: {status:1, returnDocuments:[{signedDocument:<base64>}]}
```

---

## Setup

No dependencies beyond the Python standard library and Java 8+.

```bash
# Verify Java is available
java -version

# Copy the client to your project
cp python-esign-client/esign_client.py /your/project/
```

---

## Usage

### Phase 1 — initiate signing

```python
import base64
from esign_client import ESignClient, ESignError, ESignTimeoutError

client = ESignClient(
    jar_path='/path/to/newJarEmudhra.jar',
    java_executable='java',   # or full path if java is not on PATH
    timeout=120,
)

with open('document.pdf', 'rb') as f:
    base64_doc = base64.b64encode(f.read()).decode()

result = client.get_gateway_parameter({
    'aspID':          'YOUR_ASP_ID',
    'eSignURL':       'https://esign-uat.emudhra.com/eSignRequest',    # V2 Aadhaar
    'eSignURLV2':     'https://esign-uat.emudhra.com/eSignPANRequest', # V3 PAN
    'pfxPath':        '/certs/asp-cert.pfx',
    'pfxPassword':    'your_password',
    'pfxAlias':       '1',
    'tempFolderPath': '/tmp/esign',
    'signerID':       'user@example.com',
    'responseURL':    'https://yourapp.com/esign/callback',
    'eSignType':      'V2',     # 'V2' (Aadhaar) | 'V3' (PAN)
    'authMode':       'OTP',    # 'OTP' | 'FingerPrint' | 'IRIS' | 'FaceRecognition'
    'inputs': [{
        'base64Doc':      base64_doc,
        'docInfo':        'Loan Agreement',
        'signerName':     'Jane Smith',
        'reason':         'I agree',
        'location':       'Bangalore',
        'pageTobeSigned': 'Last',         # All | Even | Odd | Last | First | PageLevel | Specify
        'appearanceType': 'StandardSignature',
        'coSign':         True,
        'inputType':      'PDF',
    }],
})

if result['status'] == 1:
    gateway_parameter    = result['gatewayParameter']
    pre_signed_temp_file = result['preSignedTempFile']
    transaction_id       = result['transactionID']
    # Redirect user to:
    # https://esign-uat.emudhra.com/eSignRequest
    #   ?eSignRequest=<gateway_parameter>
    #   &aspTxnID=<transaction_id>
    #   &Content-Type=application/xml
```

### Phase 2 — retrieve signed document

After the user signs at the gateway, eMudhra POSTs the XML to your callback URL.
Pass that XML and the temp file path from Phase 1 to complete signing.

```python
result = client.get_signed_document({
    'aspID':              'YOUR_ASP_ID',
    'eSignURL':           'https://esign-uat.emudhra.com/eSignRequest',
    'eSignURLV2':         'https://esign-uat.emudhra.com/eSignPANRequest',
    'pfxPath':            '/certs/asp-cert.pfx',
    'pfxPassword':        'your_password',
    'pfxAlias':           '1',
    'responseXML':        response_xml,         # XML POSTed by gateway to your callback
    'preSignedTempFile':  pre_signed_temp_file,  # from Phase 1
    'signedFilePath':     '/output/signed-',     # JAR writes signed-0.pdf, signed-1.pdf, ...
})

if result['status'] == 1:
    for i, doc in enumerate(result.get('returnDocuments') or []):
        if doc['status'] == 1:
            signed_pdf_b64 = doc['signedDocument']  # base64-encoded signed PDF
```

### Error handling

```python
from esign_client import ESignError, ESignTimeoutError

try:
    result = client.get_gateway_parameter({...})
except ESignTimeoutError:
    # Java process exceeded the timeout
    pass
except ESignError as e:
    # Java process failed to start, non-zero exit, or returned non-JSON
    print(e)
```

---

## Enum reference

| Field | Values |
|---|---|
| `eSignType` | `V2` (Aadhaar), `V3` (PAN) |
| `authMode` | `OTP` `FingerPrint` `IRIS` `FaceRecognition` |
| `appearanceType` | `StandardSignature` `SignatureImage` `OneLiner` `advanceSignature` `ColoredGraphic` `BackgroundImage` |
| `pageTobeSigned` | `All` `Even` `Odd` `Last` `First` `PageLevel` `Specify` |
| `coordinates` | `TopLeft` `TopMiddle` `TopRight` `CenterLeft` `CenterMiddle` `CenterRight` `BottomLeft` `BottomMiddle` `BottomRight` |
| `inputType` | `PDF` `HASH` |

**`pageLevelCoordinates` format:** `"pageNo-x,y,width,height;"` per page.
Example: `"1-400,100,150,50;2-400,100,150,50;"` signs page 1 and page 2.

---

## Requirements

- Python 3.6+
- Java 8+ (`java` on PATH or pass full path as `java_executable`)
- Built `newJarEmudhra.jar` (see root [README](../README.md) for build instructions)
