from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from claims.models import Claim
from clients.models import Client


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("cancelled", "Cancelled"),
        ("completed", "Completed"),
        ("no_show", "No show"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="appointments")
    claim = models.ForeignKey(
        Claim,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )

    start = models.DateTimeField()
    end = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="scheduled")

    location = models.TextField(blank=True)
    reason = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["start", "id"]
        constraints = [
            models.CheckConstraint(
                check=Q(end__gt=F("start")),
                name="appointment_end_after_start",
            )
        ]

    def __str__(self) -> str:
        claim_part = f" - {self.claim.claim_number}" if self.claim_id else ""
        return f"{self.start:%Y-%m-%d %H:%M}{claim_part}"

    def clean(self):
        super().clean()

        if self.end <= self.start:
            raise ValidationError({"end": "End time must be after start time."})

        overlap_qs = Appointment.objects.filter(
            start__lt=self.end,
            end__gt=self.start,
        ).exclude(pk=self.pk)

        overlap_qs = overlap_qs.exclude(status="cancelled")
        if overlap_qs.exists():
            raise ValidationError("This appointment overlaps with another appointment.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
