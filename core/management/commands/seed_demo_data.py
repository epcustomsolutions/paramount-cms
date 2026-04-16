from django.core.management.base import BaseCommand

from claims.models import Claim
from clients.models import Client


class Command(BaseCommand):
    help = "Seed demo Clients/Claims for local testing (idempotent)."

    def handle(self, *args, **options):
        data = [
            {
                "client": {
                    "first_name": "Maria",
                    "last_name": "Garcia",
                    "phone": "555-0101",
                    "email": "maria.garcia@example.com",
                    "address": "123 Maple St, Miami, FL",
                },
                "claims": [
                    {
                        "claim_number": "CLM-2024-001",
                        "status": "open",
                        "insurance_company": "State Farm",
                        "description": "Hurricane damage to roof and interior",
                        "date_of_loss": "2024-09-15",
                    },
                    {
                        "claim_number": "CLM-2024-002",
                        "status": "under_review",
                        "insurance_company": "Allstate",
                        "description": "Water damage from burst pipe",
                        "date_of_loss": "2024-11-03",
                    },
                ],
            },
            {
                "client": {
                    "first_name": "James",
                    "last_name": "Thompson",
                    "phone": "555-0202",
                    "email": "james.t@example.com",
                    "address": "88 Oak Ave, Fort Lauderdale, FL",
                },
                "claims": [
                    {
                        "claim_number": "CLM-2024-003",
                        "status": "open",
                        "insurance_company": "Citizens Property Insurance",
                        "description": "Wind damage to siding and windows",
                        "date_of_loss": "2024-10-01",
                    },
                ],
            },
            {
                "client": {
                    "first_name": "Susan",
                    "last_name": "Williams",
                    "phone": "555-0303",
                    "email": "swilliams@example.com",
                    "address": "410 Pine Rd, Orlando, FL",
                },
                "claims": [
                    {
                        "claim_number": "CLM-2025-001",
                        "status": "closed",
                        "insurance_company": "USAA",
                        "description": "Fire damage to kitchen",
                        "date_of_loss": "2025-01-12",
                    },
                    {
                        "claim_number": "CLM-2025-002",
                        "status": "denied",
                        "insurance_company": "Progressive",
                        "description": "Mold remediation",
                        "date_of_loss": "2025-02-20",
                    },
                ],
            },
        ]

        clients_created = 0
        claims_created = 0

        for entry in data:
            cd = entry["client"]
            client, created = Client.objects.get_or_create(
                first_name=cd["first_name"],
                last_name=cd["last_name"],
                defaults=cd,
            )
            if created:
                clients_created += 1

            for claim_data in entry["claims"]:
                _, claim_created = Claim.objects.get_or_create(
                    claim_number=claim_data["claim_number"],
                    defaults={**claim_data, "client": client},
                )
                if claim_created:
                    claims_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo seed complete: clients_created={clients_created}, claims_created={claims_created}"
            )
        )
