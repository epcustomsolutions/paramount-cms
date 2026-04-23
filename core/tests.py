from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse


class AuthGuardTests(TestCase):
    """Every protected app redirects anonymous users to login."""

    def test_unauthenticated_dashboard_redirects_to_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_unauthenticated_protected_urls_redirect(self):
        # Spot-check one URL from each app to catch regressions where a view
        # ships without @login_required.
        url_names = [
            "dashboard",
            ("clients:client-list", ()),
            ("claims:claim-list", ()),
            ("scheduling:schedule", ()),
            ("tools:tools-home", ()),
        ]
        for entry in url_names:
            if isinstance(entry, str):
                url = reverse(entry)
            else:
                name, args = entry
                url = reverse(name, args=args)
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    302,
                    f"{url} should redirect anonymous users",
                )
                self.assertIn("/accounts/login/", response.url)


class CheckAdminAccessCommandTests(TestCase):
    """The check_admin_access management command reports staff/superusers."""

    def test_command_lists_superuser(self):
        User = get_user_model()
        User.objects.create_superuser(
            username="eric", email="eric@example.com", password="irrelevant"
        )
        out = StringIO()
        call_command("check_admin_access", stdout=out)
        output = out.getvalue()
        self.assertIn("eric", output)
        self.assertIn("Total: 1 account(s)", output)

    def test_command_reports_empty_state(self):
        out = StringIO()
        call_command("check_admin_access", stdout=out)
        self.assertIn("No staff or superuser accounts", out.getvalue())
