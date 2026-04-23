from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from clients.models import Client

from .models import Claim, ClaimDocument


class ClaimCreationTests(TestCase):
    """CLM-YYYY-MM-VVV auto-numbering must produce unique, sequential ids."""

    def setUp(self):
        User = get_user_model()
        user = User.objects.create_user(username="tester", password="pw")
        self.client.force_login(user)
        self.customer = Client.objects.create(first_name="Dan", last_name="Smith")

    def test_create_claim_auto_numbers(self):
        response = self.client.post(
            reverse("claims:claim-create"),
            data={"client": self.customer.pk, "status": Claim.STATUS_OPEN},
        )
        self.assertEqual(response.status_code, 302)
        claim = Claim.objects.get()

        today = timezone.localdate()
        expected_prefix = f"CLM-{today.year:04d}-{today.month:02d}-"
        self.assertTrue(
            claim.claim_number.startswith(expected_prefix),
            f"got {claim.claim_number!r}, expected prefix {expected_prefix!r}",
        )
        self.assertTrue(claim.claim_number.endswith("-000"))

    def test_claim_numbers_increment_within_month(self):
        for _ in range(2):
            self.client.post(
                reverse("claims:claim-create"),
                data={"client": self.customer.pk, "status": Claim.STATUS_OPEN},
            )
        numbers = sorted(Claim.objects.values_list("claim_number", flat=True))
        self.assertEqual(len(numbers), 2)
        self.assertTrue(numbers[0].endswith("-000"))
        self.assertTrue(numbers[1].endswith("-001"))


class ClaimDocumentUploadTests(TestCase):
    """Item 1 invariant: 4 MB cap + content-type allowlist enforced server-side."""

    def setUp(self):
        User = get_user_model()
        user = User.objects.create_user(username="tester", password="pw")
        self.client.force_login(user)
        customer = Client.objects.create(first_name="Dan", last_name="Smith")
        self.claim = Claim.objects.create(client=customer)
        self.upload_url = reverse(
            "claims:claim-document-upload", args=[self.claim.pk]
        )

    def _upload(self, filename, size_bytes, content_type):
        payload = SimpleUploadedFile(
            filename,
            b"x" * size_bytes,
            content_type=content_type,
        )
        return self.client.post(self.upload_url, {"file": payload})

    def test_small_pdf_is_accepted(self):
        response = self._upload("ok.pdf", 1024, "application/pdf")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ClaimDocument.objects.count(), 1)

    def test_oversize_file_is_rejected(self):
        over = ClaimDocument.MAX_FILE_SIZE + 1
        response = self._upload("too_big.pdf", over, "application/pdf")
        # On form error the view re-renders the claim detail page (200) with
        # the error surfaced via document_form. No ClaimDocument is created.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ClaimDocument.objects.count(), 0)
        self.assertContains(response, "Max upload size")

    def test_disallowed_content_type_is_rejected(self):
        response = self._upload("note.txt", 1024, "text/plain")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ClaimDocument.objects.count(), 0)
        self.assertContains(response, "Only PDF, Word")
