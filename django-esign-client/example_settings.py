"""
example_settings.py
--------------------
Copy the ESIGN block below into your Django project's settings.py.
All keys are used by esign/client.py and esign/views.py.
"""

import os

# ── eMudhra eSign bridge configuration ───────────────────────────────────────

ESIGN = {
    # ── Bridge JAR ────────────────────────────────────────────────────────────
    # Absolute path to the compiled fat JAR.
    'JAR_PATH': os.path.join(BASE_DIR, 'bin', 'newJarEmudhra.jar'),

    # Java executable. Use a full path if 'java' is not on the server PATH.
    'JAVA_EXECUTABLE': 'java',

    # Subprocess timeout in seconds (Phase 1 and Phase 2 calls).
    'TIMEOUT': 120,

    # ── eMudhra gateway ───────────────────────────────────────────────────────
    'ASP_ID':      os.environ.get('ESIGN_ASP_ID', 'YOUR_ASP_ID'),
    'ESIGN_URL':   os.environ.get('ESIGN_URL',    'https://esign-uat.emudhra.com/eSignRequest'),    # V2 Aadhaar
    'ESIGN_URL_V2': os.environ.get('ESIGN_URL_V2', 'https://esign-uat.emudhra.com/eSignPANRequest'), # V3 PAN

    # ── ASP signing certificate ───────────────────────────────────────────────
    'PFX_PATH':     os.environ.get('ESIGN_PFX_PATH',     '/certs/asp-cert.pfx'),
    'PFX_PASSWORD': os.environ.get('ESIGN_PFX_PASSWORD', 'your_pfx_password'),
    'PFX_ALIAS':    os.environ.get('ESIGN_PFX_ALIAS',    '1'),

    # ── File paths ────────────────────────────────────────────────────────────
    # Writable temp folder for SDK work files (Phase 1 pre-signed data).
    'TEMP_FOLDER': os.environ.get('ESIGN_TEMP_FOLDER', '/tmp/esign'),

    # Directory where signed PDFs are written after Phase 2.
    'SIGNED_OUTPUT_DIR': os.environ.get('ESIGN_OUTPUT_DIR', '/var/esign/signed'),

    # ── Proxy (leave False / blank if no proxy) ───────────────────────────────
    'PROXY_REQ':           False,
    'PROXY_IP':            '',
    'PROXY_PORT':          0,
    'PROXY_USER_ID':       '',
    'PROXY_USER_PASSWORD': '',
}

# ── App registration ─────────────────────────────────────────────────────────
# Add 'esign' to INSTALLED_APPS:
INSTALLED_APPS = [
    # ... your existing apps ...
    'esign',
]

# ── Logging (optional but recommended) ───────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'esign': {
            'handlers': ['console'],
            'level': os.environ.get('ESIGN_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}
