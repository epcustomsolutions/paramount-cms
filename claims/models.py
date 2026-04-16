from django.conf import settings
from django.db import models

from clients.models import Client


class Claim(models.Model):
    STATUS_OPEN = "open"
    STATUS_UNDER_REVIEW = "under_review"
    STATUS_CLOSED = "closed"
    STATUS_DENIED = "denied"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_UNDER_REVIEW, "Under Review"),
        (STATUS_CLOSED, "Closed"),
        (STATUS_DENIED, "Denied"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="claims")
    claim_number = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    description = models.TextField(blank=True)
    insurance_company = models.CharField(max_length=200, blank=True)
    date_of_loss = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "id"]

    def __str__(self) -> str:
        return f"{self.claim_number} ({self.client.full_name})"


class ClaimNote(models.Model):
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="notes")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="claim_notes",
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Note on {self.claim.claim_number} ({self.created_at:%Y-%m-%d %H:%M})"


class ClaimDocument(models.Model):
    ALLOWED_CONTENT_TYPES = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="documents")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="claim_documents",
    )
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    file_data = models.BinaryField()
    file_size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at", "-id"]

    def __str__(self) -> str:
        return f"{self.filename} ({self.claim.claim_number})"
