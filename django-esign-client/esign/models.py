"""
esign/models.py
---------------
Stores the state that must survive the round-trip to the eMudhra gateway.

Phase 1 creates an ESignTransaction with status='initiated'.
Phase 2 callback looks it up by transaction_id and updates it to
'completed' (success) or 'failed'.
"""

import uuid

from django.db import models
from django.utils import timezone


class ESignTransaction(models.Model):
    """One eSign signing session (potentially multiple documents)."""

    class Status(models.TextChoices):
        INITIATED = 'initiated', 'Initiated'
        COMPLETED = 'completed', 'Completed'
        FAILED    = 'failed',    'Failed'

    # ── Identity ──────────────────────────────────────────────────────────────
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Transaction ID assigned by the SDK (or your app if you supply one).
    # Stored so Phase 2 can look up the right session.
    transaction_id = models.CharField(max_length=200, unique=True, db_index=True)

    # ── Phase 1 data ──────────────────────────────────────────────────────────
    # Required for Phase 2 call
    pre_signed_temp_file = models.CharField(max_length=1000)

    # Raw gateway parameter (base64 request sent to eMudhra)
    gateway_parameter = models.TextField(blank=True)

    # Signer information (for display / auditing)
    signer_id   = models.CharField(max_length=255, blank=True)
    doc_info    = models.CharField(max_length=500, blank=True)
    esign_type  = models.CharField(max_length=10, default='V2')   # V2/V3
    auth_mode   = models.CharField(max_length=30, default='OTP')

    # ── Phase 2 data ──────────────────────────────────────────────────────────
    # XML response body from the gateway callback
    response_xml = models.TextField(blank=True)

    # Paths to the signed PDF file(s) on disk (comma-separated)
    signed_file_paths = models.TextField(blank=True)

    # ── Status & errors ───────────────────────────────────────────────────────
    status        = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.INITIATED,
    )
    error_code    = models.CharField(max_length=100, blank=True)
    error_message = models.TextField(blank=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at    = models.DateTimeField(auto_now_add=True)
    completed_at  = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name        = 'eSign Transaction'
        verbose_name_plural = 'eSign Transactions'

    def __str__(self):
        return f'{self.transaction_id} [{self.status}]'

    def mark_completed(self, signed_paths=None):
        self.status       = self.Status.COMPLETED
        self.completed_at = timezone.now()
        if signed_paths:
            self.signed_file_paths = ','.join(signed_paths)
        self.save(update_fields=['status', 'completed_at', 'signed_file_paths'])

    def mark_failed(self, error_code='', error_message=''):
        self.status        = self.Status.FAILED
        self.completed_at  = timezone.now()
        self.error_code    = error_code
        self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_code', 'error_message'])
