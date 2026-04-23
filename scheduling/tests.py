from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from clients.models import Client

from .models import Appointment


class AppointmentOverlapTests(TestCase):
    """Appointment.clean() must reject overlaps with active appointments."""

    def setUp(self):
        self.customer = Client.objects.create(first_name="Dan", last_name="Smith")
        self.base = timezone.now().replace(microsecond=0) + timezone.timedelta(days=1)

    def _make(self, start_offset_min, end_offset_min, status="scheduled"):
        return Appointment(
            client=self.customer,
            start=self.base + timezone.timedelta(minutes=start_offset_min),
            end=self.base + timezone.timedelta(minutes=end_offset_min),
            status=status,
        )

    def test_overlapping_appointment_is_rejected(self):
        self._make(0, 60).save()
        overlapping = self._make(30, 90)
        with self.assertRaises(ValidationError):
            overlapping.save()
        self.assertEqual(Appointment.objects.count(), 1)

    def test_overlap_with_cancelled_appointment_is_allowed(self):
        self._make(0, 60, status="cancelled").save()
        self._make(30, 90).save()  # Should not raise.
        self.assertEqual(Appointment.objects.count(), 2)

    def test_end_before_start_is_rejected(self):
        with self.assertRaises(ValidationError):
            self._make(60, 0).save()
