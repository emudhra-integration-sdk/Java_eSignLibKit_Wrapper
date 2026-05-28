"""
example.py — full two-phase eSign workflow using ESignClient.

Replace the constants below with your actual credentials before running.
"""

import base64
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from esign_client import ESignClient, ESignError, ESignTimeoutError

# ---------------------------------------------------------------------------
# Configuration — edit these
# ---------------------------------------------------------------------------
JAR_PATH       = '../dist/newJarEmudhra.jar'
ASP_ID         = 'YOUR_ASP_ID'
ESIGN_URL      = 'https://esign-uat.emudhra.com/eSignRequest'    # V2 Aadhaar
ESIGN_URL_V2   = 'https://esign-uat.emudhra.com/eSignPANRequest' # V3 PAN
PFX_PATH       = '/certs/asp-cert.pfx'
PFX_PASSWORD   = 'your_pfx_password'
PFX_ALIAS      = '1'
TEMP_FOLDER    = '/tmp/esign'
RESPONSE_URL   = 'https://yourapp.com/esign/callback'
PDF_PATH       = '/path/to/document.pdf'
OUTPUT_DIR     = '/tmp/esign/signed'
# ---------------------------------------------------------------------------

client = ESignClient(jar_path=JAR_PATH)

# ── Phase 1 — initiate signing ─────────────────────────────────────────────

with open(PDF_PATH, 'rb') as f:
    base64_doc = base64.b64encode(f.read()).decode('utf-8')

try:
    result = client.get_gateway_parameter({
        'aspID':          ASP_ID,
        'eSignURL':       ESIGN_URL,
        'eSignURLV2':     ESIGN_URL_V2,
        'pfxPath':        PFX_PATH,
        'pfxPassword':    PFX_PASSWORD,
        'pfxAlias':       PFX_ALIAS,
        'tempFolderPath': TEMP_FOLDER,
        'signerID':       'user@example.com',
        'responseURL':    RESPONSE_URL,
        'eSignType':      'V2',
        'authMode':       'OTP',
        'inputs': [{
            'base64Doc':            base64_doc,
            'docInfo':              'Loan Agreement',
            'signerName':           'Jane Smith',
            'reason':               'I agree',
            'location':             'Bangalore',
            'pageTobeSigned':       'Last',
            'appearanceType':       'StandardSignature',
            'coSign':               True,
            'inputType':            'PDF',
        }],
    })
except ESignTimeoutError as e:
    print(f'Timeout: {e}')
    sys.exit(1)
except ESignError as e:
    print(f'Error: {e}')
    sys.exit(1)

if result.get('status') != 1:
    print(f"Phase 1 failed: {result.get('errorCode')} — {result.get('errorMessage')}")
    sys.exit(1)

gateway_parameter   = result['gatewayParameter']
pre_signed_temp_file = result['preSignedTempFile']
transaction_id      = result['transactionID']

print(f'Phase 1 OK — transactionID: {transaction_id}')
print(f'Redirect the user to: {ESIGN_URL}?eSignRequest={gateway_parameter}&aspTxnID={transaction_id}&Content-Type=application/xml')

# ── After user signs at the gateway ────────────────────────────────────────
# The gateway POSTs eSignResponse=<XML> to your RESPONSE_URL.
# Capture that XML and pass it to Phase 2.

response_xml = '<paste the gateway callback XML here>'

# ── Phase 2 — retrieve signed document ─────────────────────────────────────

os.makedirs(OUTPUT_DIR, exist_ok=True)
signed_base = os.path.join(OUTPUT_DIR, f'{transaction_id}-')

try:
    result2 = client.get_signed_document({
        'aspID':              ASP_ID,
        'eSignURL':           ESIGN_URL,
        'eSignURLV2':         ESIGN_URL_V2,
        'pfxPath':            PFX_PATH,
        'pfxPassword':        PFX_PASSWORD,
        'pfxAlias':           PFX_ALIAS,
        'responseXML':        response_xml,
        'preSignedTempFile':  pre_signed_temp_file,
        'signedFilePath':     signed_base,   # JAR writes signed-0.pdf, signed-1.pdf, ...
    })
except ESignTimeoutError as e:
    print(f'Timeout: {e}')
    sys.exit(1)
except ESignError as e:
    print(f'Error: {e}')
    sys.exit(1)

if result2.get('status') != 1:
    print(f"Phase 2 failed: {result2.get('errorCode')} — {result2.get('errorMessage')}")
    sys.exit(1)

for i, doc in enumerate(result2.get('returnDocuments') or []):
    if doc.get('status') == 1:
        out_path = f'{signed_base}{i}.pdf'
        print(f'Signed document {i}: {out_path}')
