from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Q


class Command(BaseCommand):
    help = "List every user with Django admin access (is_staff or is_superuser)."

    def handle(self, *args, **options):
        User = get_user_model()
        users = (
            User.objects.filter(Q(is_staff=True) | Q(is_superuser=True))
            .order_by("-is_superuser", "-is_staff", "username")
        )

        if not users.exists():
            self.stdout.write(
                self.style.WARNING("No staff or superuser accounts found.")
            )
            return

        self.stdout.write("Accounts with admin access:\n")
        header = (
            f"  {'username':<24} {'staff':<7} {'super':<7} "
            f"{'last login':<20} {'email'}"
        )
        self.stdout.write(header)
        self.stdout.write("  " + "-" * (len(header) - 2))

        for u in users:
            last = (
                u.last_login.strftime("%Y-%m-%d %H:%M")
                if u.last_login
                else "never"
            )
            self.stdout.write(
                f"  {u.username:<24} "
                f"{('yes' if u.is_staff else 'no'):<7} "
                f"{('yes' if u.is_superuser else 'no'):<7} "
                f"{last:<20} "
                f"{u.email}"
            )

        self.stdout.write(f"\nTotal: {users.count()} account(s)")
