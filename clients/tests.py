from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from claims.models import Claim
from scheduling.models import Appointment

from .models import Client


class ClientDeleteBlockingTests(TestCase):
    """Item 3 invariant: deleting a client with claims must be blocked."""

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="tester", password="pw")
        self.client.force_login(self.user)

    def test_delete_blocked_when_client_has_claims(self):
        customer = Client.objects.create(first_name="Dan", last_name="Smith")
        Claim.objects.create(client=customer)

        response = self.client.post(
            reverse("clients:client-delete", args=[customer.pk])
        )

        # View should render a block response (200), not delete anything.
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Client.objects.filter(pk=customer.pk).exists())
        self.assertTrue(Claim.objects.filter(client=customer).exists())

    def test_delete_succeeds_with_no_claims_and_cascades_to_appointments(self):
        customer = Client.objects.create(first_name="Pat", last_name="Jones")
        start = timezone.now() + timezone.timedelta(days=1)
        Appointment.objects.create(
            client=customer,
            start=start,
            end=start + timezone.timedelta(hours=1),
        )

        response = self.client.post(
            reverse("clients:client-delete", args=[customer.pk])
        )

        # Redirect back to the client list.
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Client.objects.filter(pk=customer.pk).exists())
        # Appointment cascade from Client is intentional; this test documents
        # that behavior so a future change to SET_NULL is surfaced.
        self.assertFalse(Appointment.objects.filter(client=customer).exists())
