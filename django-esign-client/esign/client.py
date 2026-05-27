"""
esign/client.py
---------------
Python subprocess bridge to the eMudhra eSign JAR.

Usage::

    from esign.client import ESignClient, ESignError

    client = ESignClient()

    # Phase 1
    result = client.get_gateway_parameter({
        'aspID': '...',
        'eSignURL': 'https://...',
        ...
        'inputs': [{ 'base64Doc': '...', 'docInfo': '...' }],
    })

    # Phase 2
    result = client.get_signed_document({
        'aspID': '...',
        'responseXML': '<xml>...',
        'preSignedTempFile': '/tmp/...',
    })
"""

import json
import logging
import os
import subprocess

from django.conf import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class ESignError(Exception):
    """Raised when the JAR bridge returns an error or fails to start."""


class ESignTimeoutError(ESignError):
    """Raised when the Java process exceeds the configured timeout."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class ESignClient:
    """
    Calls the eMudhra eSign bridge JAR via subprocess.

    Configuration via Django settings (all optional — sensible defaults apply)::

        ESIGN = {
            'JAR_PATH': '/abs/path/to/newJarEmudhra.jar',
            'JAVA_EXECUTABLE': 'java',          # or full path
            'TIMEOUT': 120,                     # seconds
            'ASP_ID': 'YOUR_ASP_ID',
            'ESIGN_URL': 'https://esign-uat.emudhra.com/eSignRequest',
            'ESIGN_URL_V2': 'https://esign-uat.emudhra.com/eSignPANRequest',
            'PFX_PATH': '/certs/asp-cert.pfx',
            'PFX_PASSWORD': 'secret',
            'PFX_ALIAS': '1',
            'TEMP_FOLDER': '/tmp/esign',
            'SIGNED_OUTPUT_DIR': '/var/esign/signed',
            # Proxy (optional)
            'PROXY_REQ': False,
            'PROXY_IP': '',
            'PROXY_PORT': 0,
            'PROXY_USER_ID': '',
            'PROXY_USER_PASSWORD': '',
        }
    """

    def __init__(self, jar_path=None, java_executable=None, timeout=None):
        cfg = getattr(settings, 'ESIGN', {})

        self.jar_path = (
            jar_path
            or cfg.get('JAR_PATH')
            or os.path.join(os.path.dirname(__file__), '..', '..', 'dist', 'newJarEmudhra.jar')
        )
        self.java_executable = java_executable or cfg.get('JAVA_EXECUTABLE', 'java')
        self.timeout = timeout if timeout is not None else cfg.get('TIMEOUT', 120)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _call_bridge(self, method_name, payload):
        """
        Spawn the JAR, pass *payload* as JSON, parse and return the response.

        :raises ESignTimeoutError: if process exceeds ``self.timeout`` seconds.
        :raises ESignError: on non-zero exit code or non-JSON output.
        """
        cmd = [
            self.java_executable,
            '-cp', self.jar_path,
            'org.example.NodeJSBridge',
            method_name,
            json.dumps(payload),
        ]

        logger.debug('Calling bridge: method=%s jar=%s', method_name, self.jar_path)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            raise ESignTimeoutError(
                f'Java process timed out after {self.timeout}s '
                f'(method={method_name})'
            )
        except FileNotFoundError:
            raise ESignError(
                f"Java executable not found: '{self.java_executable}'. "
                "Ensure Java 8+ is installed and on PATH."
            )

        if proc.stderr:
            logger.debug('Bridge stderr: %s', proc.stderr.strip())

        if proc.returncode != 0:
            raise ESignError(
                f'Java process exited with code {proc.returncode}. '
                f'stderr: {proc.stderr.strip()}'
            )

        raw = proc.stdout.strip()
        if not raw:
            raise ESignError(
                f'Bridge returned empty stdout. stderr: {proc.stderr.strip()}'
            )

        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ESignError(
                f'Bridge returned non-JSON output: {raw[:300]}'
            ) from exc

    def _common_creds(self):
        """Read credential defaults from Django settings."""
        cfg = getattr(settings, 'ESIGN', {})
        return {
            'aspID':            cfg.get('ASP_ID', ''),
            'eSignURL':         cfg.get('ESIGN_URL', ''),
            'eSignURLV2':       cfg.get('ESIGN_URL_V2', ''),
            'pfxPath':          cfg.get('PFX_PATH', ''),
            'pfxPassword':      cfg.get('PFX_PASSWORD', ''),
            'pfxAlias':         cfg.get('PFX_ALIAS', '1'),
            'tempFolderPath':   cfg.get('TEMP_FOLDER', '/tmp/esign'),
            'proxyReq':         cfg.get('PROXY_REQ', False),
            'proxyIp':          cfg.get('PROXY_IP', ''),
            'proxyPort':        cfg.get('PROXY_PORT', 0),
            'proxyUserID':      cfg.get('PROXY_USER_ID', ''),
            'proxyUserPassword': cfg.get('PROXY_USER_PASSWORD', ''),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_gateway_parameter(self, config):
        """
        Phase 1 — initiate signing.

        *config* keys (required unless a default is set in ``settings.ESIGN``):

        =====================  ================================================
        aspID                  eMudhra ASP ID
        eSignURL               V2 (Aadhaar) gateway URL
        eSignURLV2             V3 (PAN) gateway URL
        pfxPath                Path to ASP signing certificate (.pfx)
        pfxPassword            PFX password
        pfxAlias               PFX alias (default ``'1'``)
        tempFolderPath         Writable temp folder for SDK work files
        signerID               Signer email / identifier
        responseURL            Callback URL (eMudhra will POST XML here)
        inputs                 List of document dicts — see README
        =====================  ================================================

        Optional keys: ``redirectUrl``, ``transactionID``, ``eSignType``
        (``'V2'``/``'V3'``), ``authMode`` (``'OTP'``/``'FingerPrint'``/
        ``'IRIS'``/``'FaceRecognition'``), proxy settings,
        ``sessionTimeout``, ``signatureContents``.

        :returns: ``eSignServiceReturn`` as a Python dict.
                  Check ``result['status'] == 1`` for success.
        """
        payload = {**self._common_creds(), **config}

        # Defaults for optional fields
        payload.setdefault('redirectUrl', payload.get('responseURL', ''))
        payload.setdefault('transactionID', '')
        payload.setdefault('eSignType', 'V2')
        payload.setdefault('authMode', 'OTP')
        payload.setdefault('inputs', [])
        payload.setdefault('sessionTimeout', 0)
        payload.setdefault('signatureContents', 0)

        logger.info(
            'get_gateway_parameter: signerID=%s eSignType=%s docs=%d',
            payload.get('signerID'), payload.get('eSignType'),
            len(payload.get('inputs', [])),
        )
        return self._call_bridge('getGatewayParameter', payload)

    def get_signed_document(self, config):
        """
        Phase 2 — retrieve signed document.

        Required *config* keys:

        =====================  ================================================
        responseXML            Full XML body POSTed by eMudhra to your callback
        preSignedTempFile      Temp file path returned by Phase 1
        =====================  ================================================

        Optional: ``signedFilePath`` (base path for writing signed PDFs to
        disk, e.g. ``'/var/esign/signed-'`` → writes
        ``signed-0.pdf``, ``signed-1.pdf``, …).
        Credential keys follow the same rules as :meth:`get_gateway_parameter`.

        :returns: ``eSignServiceReturn`` as a Python dict.
        """
        payload = {**self._common_creds(), **config}
        payload.setdefault('signedFilePath', '')
        payload.setdefault('sessionTimeout', 0)
        payload.setdefault('signatureContents', 0)

        logger.info(
            'get_signed_document: tempFile=%s',
            payload.get('preSignedTempFile'),
        )
        return self._call_bridge('getSignedDocument', payload)
