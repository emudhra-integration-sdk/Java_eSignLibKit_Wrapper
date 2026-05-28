"""
esign_client.py
---------------
Python subprocess wrapper for the eMudhra eSign bridge JAR.

Works with any Python 3.6+ project — no web framework required.

Usage
-----
    from esign_client import ESignClient

    client = ESignClient('/path/to/newJarEmudhra.jar')

    # Phase 1 — initiate signing
    result = client.get_gateway_parameter({
        'aspID':          'YOUR_ASP_ID',
        'eSignURL':       'https://esign-uat.emudhra.com/eSignRequest',
        'eSignURLV2':     'https://esign-uat.emudhra.com/eSignPANRequest',
        'pfxPath':        '/certs/asp-cert.pfx',
        'pfxPassword':    'password',
        'pfxAlias':       '1',
        'tempFolderPath': '/tmp/esign',
        'signerID':       'user@example.com',
        'responseURL':    'https://yourapp.com/esign/callback',
        'eSignType':      'V2',
        'authMode':       'OTP',
        'inputs': [{
            'base64Doc':            '<base64-encoded PDF>',
            'docInfo':              'Loan Agreement',
            'pageTobeSigned':       'Last',
            'appearanceType':       'StandardSignature',
            'coSign':               True,
            'inputType':            'PDF',
        }],
    })
    if result['status'] == 1:
        gateway_param     = result['gatewayParameter']
        pre_signed_file   = result['preSignedTempFile']
        transaction_id    = result['transactionID']

    # Phase 2 — retrieve signed document
    result = client.get_signed_document({
        'aspID':              'YOUR_ASP_ID',
        'eSignURL':           'https://esign-uat.emudhra.com/eSignRequest',
        'eSignURLV2':         'https://esign-uat.emudhra.com/eSignPANRequest',
        'pfxPath':            '/certs/asp-cert.pfx',
        'pfxPassword':        'password',
        'pfxAlias':           '1',
        'responseXML':        '<XML from gateway callback>',
        'preSignedTempFile':  '/tmp/esign/TXN-001.tmp',
        'signedFilePath':     '/output/signed-',  # writes signed-0.pdf, signed-1.pdf, ...
    })
    if result['status'] == 1:
        for doc in result.get('returnDocuments', []):
            signed_b64 = doc['signedDocument']   # base64-encoded signed PDF
"""

import json
import os
import subprocess


class ESignError(Exception):
    """Raised when the JAR bridge returns an error or fails to start."""


class ESignTimeoutError(ESignError):
    """Raised when the Java process exceeds the configured timeout."""


class ESignClient:
    """
    Calls the eMudhra eSign bridge JAR via subprocess.

    Parameters
    ----------
    jar_path : str
        Absolute path to ``newJarEmudhra.jar``.
        Defaults to ``../dist/newJarEmudhra.jar`` relative to this file.
    java_executable : str
        Java command (default ``'java'``). Use a full path if Java is not on PATH.
    timeout : int
        Subprocess timeout in seconds (default ``120``). Pass ``0`` to disable.
    """

    def __init__(self, jar_path=None, java_executable='java', timeout=120):
        self.jar_path = jar_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..', 'dist', 'newJarEmudhra.jar',
        )
        self.java_executable = java_executable
        self.timeout = timeout or None  # subprocess.run wants None for no timeout

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _call_bridge(self, method_name, payload):
        cmd = [
            self.java_executable,
            '-cp', self.jar_path,
            'org.example.NodeJSBridge',
            method_name,
            json.dumps(payload),
        ]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            raise ESignTimeoutError(
                f'Java process timed out after {self.timeout}s (method={method_name})'
            )
        except FileNotFoundError:
            raise ESignError(
                f"Java executable not found: '{self.java_executable}'. "
                "Ensure Java 8+ is installed and on PATH."
            )

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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_gateway_parameter(self, config):
        """
        Phase 1 — initiate signing.

        Pass the full signing config dict. All keys are forwarded directly
        to the JAR; see the project README for the complete JSON schema.

        Returns the ``eSignServiceReturn`` deserialized as a Python dict.
        Check ``result['status'] == 1`` for success.
        """
        payload = dict(config)
        payload.setdefault('redirectUrl', payload.get('responseURL', ''))
        payload.setdefault('transactionID', '')
        payload.setdefault('eSignType', 'V2')
        payload.setdefault('authMode', 'OTP')
        payload.setdefault('inputs', [])
        payload.setdefault('proxyReq', False)
        payload.setdefault('proxyIp', '')
        payload.setdefault('proxyPort', 0)
        payload.setdefault('proxyUserID', '')
        payload.setdefault('proxyUserPassword', '')
        payload.setdefault('sessionTimeout', 0)
        payload.setdefault('signatureContents', 0)
        return self._call_bridge('getGatewayParameter', payload)

    def get_signed_document(self, config):
        """
        Phase 2 — retrieve signed document.

        Pass ``responseXML`` (gateway callback body) and
        ``preSignedTempFile`` (path returned by Phase 1).

        Returns the ``eSignServiceReturn`` deserialized as a Python dict.
        """
        payload = dict(config)
        payload.setdefault('signedFilePath', '')
        payload.setdefault('proxyReq', False)
        payload.setdefault('proxyIp', '')
        payload.setdefault('proxyPort', 0)
        payload.setdefault('proxyUserID', '')
        payload.setdefault('proxyUserPassword', '')
        payload.setdefault('sessionTimeout', 0)
        payload.setdefault('signatureContents', 0)
        return self._call_bridge('getSignedDocument', payload)
