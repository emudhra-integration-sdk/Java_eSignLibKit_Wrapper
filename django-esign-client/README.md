# eMudhra eSign — Django Integration

A reusable Django app that integrates the eMudhra eSign bridge JAR into
any Django project. Supports Aadhaar (V2) and PAN (V3) based digital signing.

---

## How it works

```
Browser / API client
      │
      │  POST /esign/initiate/  {pdf, signer_id, ...}
      ▼
Django  ──► ESignClient.get_gateway_parameter()
              ──► subprocess: java -cp newJarEmudhra.jar NodeJSBridge
                               getGatewayParameter '{"aspID":...}'
              ◄── JSON: {status:1, gatewayParameter, preSignedTempFile, ...}
      │
      │  Saves ESignTransaction (status=initiated)
      │  Returns gateway_url to client
      │
      ▼
Client redirects user to eMudhra gateway URL
      │
      │  User authenticates (OTP / fingerprint) and signs
      │
      ▼
eMudhra gateway  POST /esign/callback/  eSignResponse=<XML>
      │
      ▼
Django  ──► ESignClient.get_signed_document()
              ──► subprocess: java ... getSignedDocument '{"responseXML":...}'
              ◄── JSON: {status:1, returnDocuments:[{signedDocument:<base64>}]}
      │
      │  Writes signed PDF to SIGNED_OUTPUT_DIR
      │  Updates ESignTransaction (status=completed)
      │  Returns HTTP 200 (ACK to gateway)
      │
      ▼
Client polls GET /esign/status/<transaction_id>/
      │  → {status: "completed", signed_docs: 1}
      ▼
Client fetches GET /esign/download/<transaction_id>/
      │  → streams signed PDF
```

---

## Quick Setup

### 1. Copy the app

```bash
cp -r django-esign-client/esign  /your/django/project/esign
```

### 2. Install dependencies

```bash
pip install -r django-esign-client/requirements.txt
```

### 3. Configure settings.py

Copy the `ESIGN` dict from `example_settings.py` into your `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'esign',
]

ESIGN = {
    'JAR_PATH':     '/path/to/newJarEmudhra.jar',
    'JAVA_EXECUTABLE': 'java',
    'TIMEOUT':      120,

    'ASP_ID':       'YOUR_ASP_ID',
    'ESIGN_URL':    'https://esign-uat.emudhra.com/eSignRequest',    # V2
    'ESIGN_URL_V2': 'https://esign-uat.emudhra.com/eSignPANRequest', # V3

    'PFX_PATH':     '/certs/asp-cert.pfx',
    'PFX_PASSWORD': 'your-password',
    'PFX_ALIAS':    '1',

    'TEMP_FOLDER':      '/tmp/esign',
    'SIGNED_OUTPUT_DIR': '/var/esign/signed',
}
```

### 4. Wire up URLs

```python
# project/urls.py
from django.urls import path, include

urlpatterns = [
    path('esign/', include('esign.urls')),
    ...
]
```

### 5. Run migrations

```bash
python manage.py migrate esign
```

---

## API Endpoints

### `POST /esign/initiate/`

Starts signing for one document.

**Multipart form upload:**

```bash
curl -X POST https://yourapp.com/esign/initiate/ \
  -F "pdf=@/path/to/document.pdf" \
  -F "signer_id=user@example.com" \
  -F "doc_info=Loan Agreement" \
  -F "esign_type=V2" \
  -F "auth_mode=OTP" \
  -F "page_coordinates=1-400,100,150,50;"
```

**JSON body:**

```bash
curl -X POST https://yourapp.com/esign/initiate/ \
  -H "Content-Type: application/json" \
  -d '{
    "signer_id":        "user@example.com",
    "doc_info":         "Loan Agreement",
    "base64_doc":       "<base64-encoded PDF>",
    "esign_type":       "V2",
    "auth_mode":        "OTP",
    "page_coordinates": "1-400,100,150,50;",
    "appearance_type":  "StandardSignature"
  }'
```

**Response:**

```json
{
    "success": true,
    "transaction_id": "TXN-2024-ABC123",
    "gateway_parameter": "<base64 eSign request>",
    "gateway_url": "https://esign-uat.emudhra.com/esign?eSignRequest=..."
}
```

Redirect the user's browser to `gateway_url`. Store `transaction_id` to
poll status later.

---

### `POST /esign/callback/`

**Called by the eMudhra gateway** after the user signs — do not call this
yourself. The gateway POSTs `eSignResponse=<URL-encoded XML>` to this URL.

- Requires the URL to be publicly reachable (no localhost).
- No CSRF token needed (the view exempts it automatically).
- Always returns `HTTP 200` as an ACK to the gateway.

---

### `GET /esign/status/<transaction_id>/`

Poll this after redirecting the user to check if signing completed.

```bash
curl https://yourapp.com/esign/status/TXN-2024-ABC123/
```

```json
{
    "transaction_id": "TXN-2024-ABC123",
    "status":         "completed",
    "signer_id":      "user@example.com",
    "doc_info":       "Loan Agreement",
    "esign_type":     "V2",
    "error_code":     "",
    "error_message":  "",
    "signed_docs":    1,
    "created_at":     "2024-01-01T12:00:00+05:30",
    "completed_at":   "2024-01-01T12:05:30+05:30"
}
```

`status` values: `initiated` · `completed` · `failed`

---

### `GET /esign/download/<transaction_id>/`

Streams the signed PDF. Use `?doc=1` for the second document (0-based).

```bash
curl -O -J https://yourapp.com/esign/download/TXN-2024-ABC123/
```

---

## Advanced Usage

### Multiple documents

Use `ESignClient` directly and pass multiple items in `inputs`:

```python
from esign.client import ESignClient
import base64

client = ESignClient()

result = client.get_gateway_parameter({
    'signerID':    'user@example.com',
    'responseURL': 'https://yourapp.com/esign/callback/',
    'eSignType':   'V2',
    'authMode':    'OTP',
    'inputs': [
        {
            'base64Doc':            base64.b64encode(open('doc1.pdf','rb').read()).decode(),
            'docInfo':              'Agreement',
            'signerName':           'Jane Smith',
            'reason':               'I agree',
            'location':             'Bangalore',
            'pageTobeSigned':       'PageLevel',
            'pageLevelCoordinates': '1-400,100,150,50;',
            'appearanceType':       'StandardSignature',
            'coSign':               True,
            'inputType':            'PDF',
        },
        {
            'base64Doc':            base64.b64encode(open('doc2.pdf','rb').read()).decode(),
            'docInfo':              'Annexure',
            'pageTobeSigned':       'Last',
            'coordinates':          'BottomRight',
            'appearanceType':       'StandardSignature',
            'coSign':               True,
            'inputType':            'PDF',
        },
    ],
})
```

### Custom post-signing logic

Subclass `ESignCallbackView` and override `on_signed`:

```python
# myapp/views.py
from esign.views import ESignCallbackView
from myapp.tasks import send_signed_document_email

class MyCallbackView(ESignCallbackView):
    def on_signed(self, transaction, result, signed_paths):
        # Send email, trigger webhook, update your own model, etc.
        send_signed_document_email.delay(
            to=transaction.signer_id,
            pdf_path=signed_paths[0] if signed_paths else None,
        )
```

```python
# myapp/urls.py
from django.urls import path, include
from myapp.views import MyCallbackView

urlpatterns = [
    path('esign/', include('esign.urls')),
    path('esign/callback/', MyCallbackView.as_view()),  # override callback only
]
```

### Using URL-mode input (no base64 upload)

If the PDF is hosted at a URL, set `docURL` instead of `base64Doc`:

```python
result = client.get_gateway_parameter({
    ...
    'inputs': [{
        'base64Doc': '',
        'docURL':    'https://yourapp.com/documents/agreement.pdf',
        'docInfo':   'Agreement',
        ...
    }],
})
```

### Hash mode (send only SHA-256, not full PDF)

```python
import hashlib, base64

with open('document.pdf', 'rb') as f:
    content = f.read()

doc_hash = hashlib.sha256(content).hexdigest()

result = client.get_gateway_parameter({
    ...
    'inputs': [{
        'docHash':   doc_hash,
        'inputType': 'HASH',
        'docInfo':   'Agreement',
        ...
    }],
})
```

---

## Enum reference

| Field | Values |
|---|---|
| `eSignType` / `esign_type` | `V2` (Aadhaar), `V3` (PAN) |
| `authMode` / `auth_mode` | `OTP` `FingerPrint` `IRIS` `FaceRecognition` |
| `appearanceType` | `StandardSignature` `SignatureImage` `OneLiner` `advanceSignature` `ColoredGraphic` `BackgroundImage` |
| `pageTobeSigned` | `All` `Even` `Odd` `Last` `First` `PageLevel` `Specify` |
| `coordinates` | `TopLeft` `TopMiddle` `TopRight` `CenterLeft` `CenterMiddle` `CenterRight` `BottomLeft` `BottomMiddle` `BottomRight` |

**`pageLevelCoordinates` format:** `"pageNo-x,y,width,height;"` per page.  
Example: `"1-400,100,150,50;2-400,100,150,50;"` — sign on page 1 and page 2.

---

## Environment variables

All sensitive credentials can be kept out of `settings.py` using env vars:

```bash
export ESIGN_ASP_ID=YOUR_ASP_ID
export ESIGN_URL=https://esign.emudhra.com/eSignRequest
export ESIGN_URL_V2=https://esign.emudhra.com/eSignPANRequest
export ESIGN_PFX_PATH=/certs/asp-cert.pfx
export ESIGN_PFX_PASSWORD=secret
export ESIGN_TEMP_FOLDER=/tmp/esign
export ESIGN_OUTPUT_DIR=/var/esign/signed
```

---

## Production checklist

- [ ] `ESIGN['TEMP_FOLDER']` and `ESIGN['SIGNED_OUTPUT_DIR']` exist and are writable by the Django process
- [ ] `ESIGN['JAR_PATH']` points to the built fat JAR
- [ ] `java` is on the server PATH (`java -version` works as the Django user)
- [ ] The callback URL (`/esign/callback/`) is publicly reachable by eMudhra servers
- [ ] PFX certificate and ASP ID are valid (obtained from eMudhra)
- [ ] All credentials are in environment variables, not hardcoded
- [ ] `python manage.py migrate esign` has been run
- [ ] Temp and output directories are excluded from backups of sensitive data (signed PDFs may contain personal info)
