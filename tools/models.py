from typing import Optional

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class MileageEntry(models.Model):
    """
    One trip entry, storing start and end odometer readings.
    This allows later audit/tax reporting while keeping the UI simple.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()

    start_mileage = models.PositiveIntegerField(null=True, blank=True)
    start_recorded_at = models.DateTimeField(null=True, blank=True)

    end_mileage = models.PositiveIntegerField(null=True, blank=True)
    end_recorded_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-start_mileage", "-id"]

    @property
    def total_mileage(self) -> Optional[int]:
        if self.start_mileage is None or self.end_mileage is None:
            return None
        return self.end_mileage - self.start_mileage

    def clean(self):
        # Ensure start is set before end.
        if self.end_mileage is not None and self.start_mileage is None:
            raise ValidationError({"start_mileage": "Start mileage is required before setting end."})

        if self.start_mileage is not None and self.end_mileage is not None:
            if self.end_mileage < self.start_mileage:
                raise ValidationError({"end_mileage": "End mileage must be greater than or equal to start."})

    def __str__(self) -> str:
        return f"{self.date} ({self.user})"
