"""
esign/views.py
--------------
Django views for the two-phase eMudhra eSign workflow.

URL wiring example (in your urls.py)::

    from django.urls import path, include
    urlpatterns = [
        path('esign/', include('esign.urls')),
    ]

Flow
----
1. POST /esign/initiate/
   ↳ Reads PDF upload (or base64 from JSON body)
   ↳ Calls Phase 1 → gets gatewayParameter
   ↳ Saves ESignTransaction
   ↳ Returns JSON with gatewayParameter + redirect URL

2. POST /esign/callback/          ← eMudhra gateway posts here
   ↳ Reads eSignResponse XML from POST body
   ↳ Looks up ESignTransaction by transactionID in the XML
   ↳ Calls Phase 2 → gets signed PDF
   ↳ Updates ESignTransaction
   ↳ Returns 200 OK (eMudhra gateway reads this as ACK)

3. GET  /esign/status/<transaction_id>/
   ↳ Returns current status of a transaction as JSON

4. GET  /esign/download/<transaction_id>/
   ↳ Streams the signed PDF to the browser (doc index via ?doc=0)
"""

import base64
import json
import logging
import os
import re

from django.conf import settings
from django.http import (
    FileResponse,
    HttpResponse,
    JsonResponse,
)
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .client import ESignClient, ESignError, ESignTimeoutError
from .models import ESignTransaction

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cfg(key, default=None):
    """Read a value from settings.ESIGN dict."""
    return getattr(settings, 'ESIGN', {}).get(key, default)


def _json_error(message, status=400):
    return JsonResponse({'success': False, 'error': message}, status=status)


def _extract_transaction_id(xml_text):
    """
    Pull transactionID out of the eMudhra eSign response XML.
    The element name varies slightly across versions — try a few patterns.
    """
    for pattern in (
        r'<transactionID[^>]*>([^<]+)</transactionID>',
        r'<TransactionID[^>]*>([^<]+)</TransactionID>',
        r'transactionID="([^"]+)"',
    ):
        match = re.search(pattern, xml_text)
        if match:
            return match.group(1).strip()
    return None


# ---------------------------------------------------------------------------
# View 1 — Initiate signing  (POST /esign/initiate/)
# ---------------------------------------------------------------------------

class ESignInitiateView(View):
    """
    Starts the eSign workflow for one or more documents.

    Accepts **multipart/form-data** (PDF file upload) or
    **application/json** (base64-encoded PDF).

    Multipart form fields
    ~~~~~~~~~~~~~~~~~~~~~
    ``pdf``              — uploaded PDF file (required unless using JSON body)
    ``signer_id``        — signer email/identifier (required)
    ``doc_info``         — document description (optional)
    ``esign_type``       — ``V2`` or ``V3`` (default: ``V2``)
    ``auth_mode``        — ``OTP`` / ``FingerPrint`` / ``IRIS`` / ``FaceRecognition``
    ``response_url``     — override default callback URL
    ``page_coordinates`` — e.g. ``1-400,100,150,50;``
    ``appearance_type``  — e.g. ``StandardSignature``

    JSON body alternative
    ~~~~~~~~~~~~~~~~~~~~~
    ::

        {
            "signer_id": "user@example.com",
            "doc_info": "Loan Agreement",
            "base64_doc": "<base64-encoded PDF>",
            "esign_type": "V2",
            "auth_mode": "OTP",
            "page_coordinates": "1-400,100,150,50;",
            "appearance_type": "StandardSignature",
            "response_url": "https://yourapp.com/esign/callback/"
        }

    Response (JSON)
    ~~~~~~~~~~~~~~~
    ::

        {
            "success": true,
            "transaction_id": "TXN-...",
            "gateway_parameter": "<base64 eSign request>",
            "gateway_url": "https://esign-uat.emudhra.com/esign?eSignRequest=..."
        }
    """

    def post(self, request):
        content_type = request.content_type or ''

        # ── Parse input ───────────────────────────────────────────────────────
        if 'application/json' in content_type:
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return _json_error('Invalid JSON body.')
            base64_doc  = data.get('base64_doc', '')
            signer_id   = data.get('signer_id', '')
            doc_info    = data.get('doc_info', 'Document')
            esign_type  = data.get('esign_type', 'V2')
            auth_mode   = data.get('auth_mode', 'OTP')
            page_coords = data.get('page_coordinates', '1-400,100,150,50;')
            appear_type = data.get('appearance_type', 'StandardSignature')
            response_url = data.get('response_url', '')
        else:
            # multipart/form-data
            signer_id   = request.POST.get('signer_id', '')
            doc_info    = request.POST.get('doc_info', 'Document')
            esign_type  = request.POST.get('esign_type', 'V2')
            auth_mode   = request.POST.get('auth_mode', 'OTP')
            page_coords = request.POST.get('page_coordinates', '1-400,100,150,50;')
            appear_type = request.POST.get('appearance_type', 'StandardSignature')
            response_url = request.POST.get('response_url', '')
            pdf_file    = request.FILES.get('pdf')

            if not pdf_file:
                return _json_error('No PDF file uploaded. Use field name "pdf".')
            base64_doc = base64.b64encode(pdf_file.read()).decode('utf-8')

        if not signer_id:
            return _json_error('"signer_id" is required.')
        if not base64_doc:
            return _json_error('No document provided.')

        # ── Resolve callback URL ───────────────────────────────────────────────
        if not response_url:
            response_url = request.build_absolute_uri('/esign/callback/')

        # ── Call Phase 1 ──────────────────────────────────────────────────────
        client = ESignClient()
        try:
            result = client.get_gateway_parameter({
                'signerID':    signer_id,
                'responseURL': response_url,
                'eSignType':   esign_type,
                'authMode':    auth_mode,
                'inputs': [{
                    'base64Doc':            base64_doc,
                    'docInfo':              doc_info,
                    'signerName':           signer_id,
                    'pageTobeSigned':       'PageLevel',
                    'pageLevelCoordinates': page_coords,
                    'appearanceType':       appear_type,
                    'coSign':               True,
                    'inputType':            'PDF',
                }],
            })
        except ESignTimeoutError as exc:
            logger.error('eSign Phase 1 timeout: %s', exc)
            return _json_error('eSign service timed out. Please try again.', status=504)
        except ESignError as exc:
            logger.error('eSign Phase 1 error: %s', exc)
            return _json_error(f'eSign service error: {exc}', status=502)

        if result.get('status') != 1:
            logger.warning(
                'Phase 1 returned failure: code=%s msg=%s',
                result.get('errorCode'), result.get('errorMessage'),
            )
            return _json_error(
                result.get('errorMessage', 'Unknown eSign error'),
                status=502,
            )

        # ── Persist transaction ────────────────────────────────────────────────
        txn = ESignTransaction.objects.create(
            transaction_id       = result['transactionID'],
            pre_signed_temp_file = result['preSignedTempFile'],
            gateway_parameter    = result.get('gatewayParameter', ''),
            signer_id            = signer_id,
            doc_info             = doc_info,
            esign_type           = esign_type,
            auth_mode            = auth_mode,
        )
        logger.info('Created ESignTransaction %s for signer %s', txn.transaction_id, signer_id)

        # Build the gateway redirect URL
        gateway_base = (
            _cfg('ESIGN_URL') if esign_type == 'V2' else _cfg('ESIGN_URL_V2')
        )
        gateway_url = f"{gateway_base}?eSignRequest={result['gatewayParameter']}&aspTxnID={txn.transaction_id}&Content-Type=application/xml"

        return JsonResponse({
            'success':           True,
            'transaction_id':    txn.transaction_id,
            'gateway_parameter': result['gatewayParameter'],
            'gateway_url':       gateway_url,
        })


# ---------------------------------------------------------------------------
# View 2 — Gateway callback  (POST /esign/callback/)
# ---------------------------------------------------------------------------

@method_decorator(csrf_exempt, name='dispatch')  # eMudhra gateway won't send CSRF token
class ESignCallbackView(View):
    """
    Receives the XML response POSTed by the eMudhra gateway after signing.

    eMudhra typically sends:
    - POST body: ``eSignResponse=<URL-encoded XML>``
    - Or raw XML in the request body

    This view:
    1. Extracts the transaction ID from the XML
    2. Looks up the ESignTransaction
    3. Calls Phase 2 (get_signed_document)
    4. Saves signed PDFs to ESIGN['SIGNED_OUTPUT_DIR']
    5. Updates the ESignTransaction record
    6. Returns HTTP 200 (eMudhra checks this as an ACK)

    Override ``on_signed()`` to add custom post-signing logic
    (e.g. email notification, webhook, database update).
    """

    def post(self, request):
        # eMudhra posts the XML as form field 'eSignResponse' or raw body
        response_xml = (
            request.POST.get('eSignResponse')
            or request.body.decode('utf-8', errors='replace')
        )

        if not response_xml:
            logger.error('eSign callback received empty body')
            return HttpResponse('Empty response', status=400)

        # Extract transaction ID
        transaction_id = _extract_transaction_id(response_xml)
        if not transaction_id:
            logger.error('Could not extract transactionID from gateway XML')
            return HttpResponse('Missing transactionID', status=400)

        # Look up transaction
        try:
            txn = ESignTransaction.objects.get(transaction_id=transaction_id)
        except ESignTransaction.DoesNotExist:
            logger.error('No ESignTransaction found for transactionID=%s', transaction_id)
            return HttpResponse('Unknown transaction', status=404)

        if txn.status != ESignTransaction.Status.INITIATED:
            logger.warning(
                'Callback for already-processed transaction %s (status=%s)',
                transaction_id, txn.status,
            )
            return HttpResponse('Already processed', status=200)

        # Save raw XML for audit
        txn.response_xml = response_xml
        txn.save(update_fields=['response_xml'])

        # ── Phase 2 ───────────────────────────────────────────────────────────
        output_dir  = _cfg('SIGNED_OUTPUT_DIR', '/tmp/esign/signed')
        signed_base = os.path.join(output_dir, f'{transaction_id}-')
        os.makedirs(output_dir, exist_ok=True)

        client = ESignClient()
        try:
            result = client.get_signed_document({
                'responseXML':      response_xml,
                'preSignedTempFile': txn.pre_signed_temp_file,
                'signedFilePath':   signed_base,
            })
        except ESignTimeoutError as exc:
            logger.error('eSign Phase 2 timeout for txn %s: %s', transaction_id, exc)
            txn.mark_failed('TIMEOUT', str(exc))
            return HttpResponse('eSign timeout', status=504)
        except ESignError as exc:
            logger.error('eSign Phase 2 error for txn %s: %s', transaction_id, exc)
            txn.mark_failed('BRIDGE_ERROR', str(exc))
            return HttpResponse('eSign error', status=502)

        if result.get('status') != 1:
            txn.mark_failed(
                result.get('errorCode', 'ESIGN_ERROR'),
                result.get('errorMessage', 'Signing failed'),
            )
            logger.warning(
                'Phase 2 failure for txn %s: %s - %s',
                transaction_id, result.get('errorCode'), result.get('errorMessage'),
            )
            return HttpResponse('Signing failed', status=200)  # still ACK to gateway

        # Collect paths of saved signed PDFs
        signed_paths = []
        for i, doc in enumerate(result.get('returnDocuments') or []):
            if doc.get('status') == 1:
                path = f'{signed_base}{i}.pdf'
                if os.path.exists(path):
                    signed_paths.append(path)

        txn.mark_completed(signed_paths)
        logger.info(
            'Phase 2 complete for txn %s — %d signed doc(s)',
            transaction_id, len(signed_paths),
        )

        # Hook for subclasses
        self.on_signed(txn, result, signed_paths)

        return HttpResponse('OK', status=200)

    def on_signed(self, transaction, result, signed_paths):
        """
        Called after successful signing. Override in a subclass to add
        custom logic (email, webhook, update your own models, etc.).

        :param transaction: :class:`ESignTransaction` instance (already saved)
        :param result:      Raw Phase 2 response dict from the bridge
        :param signed_paths: List of absolute paths to signed PDF files
        """
        pass  # no-op by default


# ---------------------------------------------------------------------------
# View 3 — Transaction status  (GET /esign/status/<transaction_id>/)
# ---------------------------------------------------------------------------

class ESignStatusView(View):
    """
    Returns the current status of an eSign transaction.

    Response::

        {
            "transaction_id": "TXN-...",
            "status": "completed",       // initiated | completed | failed
            "signer_id": "user@example.com",
            "doc_info": "Loan Agreement",
            "error_code": "",
            "error_message": "",
            "signed_docs": 1,
            "created_at": "2024-01-01T12:00:00Z",
            "completed_at": "2024-01-01T12:05:00Z"
        }
    """

    def get(self, request, transaction_id):
        try:
            txn = ESignTransaction.objects.get(transaction_id=transaction_id)
        except ESignTransaction.DoesNotExist:
            return _json_error('Transaction not found.', status=404)

        signed_count = (
            len([p for p in txn.signed_file_paths.split(',') if p])
            if txn.signed_file_paths else 0
        )

        return JsonResponse({
            'transaction_id': txn.transaction_id,
            'status':         txn.status,
            'signer_id':      txn.signer_id,
            'doc_info':       txn.doc_info,
            'esign_type':     txn.esign_type,
            'error_code':     txn.error_code,
            'error_message':  txn.error_message,
            'signed_docs':    signed_count,
            'created_at':     txn.created_at.isoformat(),
            'completed_at':   txn.completed_at.isoformat() if txn.completed_at else None,
        })


# ---------------------------------------------------------------------------
# View 4 — Download signed PDF  (GET /esign/download/<transaction_id>/)
# ---------------------------------------------------------------------------

class ESignDownloadView(View):
    """
    Streams a signed PDF to the browser.

    Query params:
    - ``doc`` — 0-based document index (default ``0``)

    Returns 404 if the transaction is not completed or the file is missing.
    """

    def get(self, request, transaction_id):
        try:
            txn = ESignTransaction.objects.get(transaction_id=transaction_id)
        except ESignTransaction.DoesNotExist:
            return _json_error('Transaction not found.', status=404)

        if txn.status != ESignTransaction.Status.COMPLETED:
            return _json_error(
                f'Document not ready. Transaction status: {txn.status}',
                status=409,
            )

        paths = [p for p in txn.signed_file_paths.split(',') if p]
        if not paths:
            return _json_error('No signed files on record.', status=404)

        doc_index = int(request.GET.get('doc', 0))
        if doc_index >= len(paths):
            return _json_error(
                f'Document index {doc_index} out of range (0–{len(paths) - 1}).',
                status=404,
            )

        file_path = paths[doc_index]
        if not os.path.exists(file_path):
            return _json_error('Signed file not found on server.', status=404)

        filename = f'signed-{txn.transaction_id}-{doc_index}.pdf'
        response = FileResponse(
            open(file_path, 'rb'),
            content_type='application/pdf',
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
