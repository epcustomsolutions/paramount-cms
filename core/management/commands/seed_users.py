import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from typing import Optional


class Command(BaseCommand):
    help = "Seed initial users from environment variables."

    def handle(self, *args, **options):
        User = get_user_model()

        def env(name: str) -> Optional[str]:
            value = os.environ.get(name)
            if value is None:
                return None
            value = value.strip()
            return value or None

        super_username = env("SEED_SUPERUSER_USERNAME")
        super_email = env("SEED_SUPERUSER_EMAIL")
        super_password = env("SEED_SUPERUSER_PASSWORD")

        staff_username = env("SEED_STAFF_USERNAME") or env("SEED_VET_USERNAME")
        staff_email = env("SEED_STAFF_EMAIL") or env("SEED_VET_EMAIL") or staff_username
        staff_password = env("SEED_STAFF_PASSWORD") or env("SEED_VET_PASSWORD")

        created = 0

        def upsert_user(*, username: str, email: Optional[str], password: str, **flags):
            nonlocal created
            user, was_created = User.objects.get_or_create(
                username=username,
                defaults={"email": email or "", **flags},
            )
            if not was_created:
                for k, v in flags.items():
                    setattr(user, k, v)

            if password:
                user.set_password(password)
            if email is not None:
                user.email = email
            user.save()

            if was_created:
                created += 1

        if super_username and super_email and super_password:
            upsert_user(
                username=super_username,
                email=super_email,
                password=super_password,
                is_staff=True,
                is_superuser=True,
            )
            self.stdout.write(self.style.SUCCESS(f"Superuser ensured: {super_username}"))
        else:
            self.stdout.write(
                "Skipping superuser seed. Set SEED_SUPERUSER_USERNAME/EMAIL/PASSWORD."
            )

        if staff_username and staff_password:
            upsert_user(
                username=staff_username,
                email=staff_email,
                password=staff_password,
                is_staff=True,
                is_superuser=False,
            )
            self.stdout.write(self.style.SUCCESS(f"Staff user ensured: {staff_username}"))
        else:
            self.stdout.write(
                "Skipping staff user seed. Set SEED_STAFF_USERNAME and SEED_STAFF_PASSWORD."
            )

        self.stdout.write(self.style.NOTICE(f"User create/update complete (created {created})."))

