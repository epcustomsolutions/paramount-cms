from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from claims.models import Claim, ClaimNote
from clients.models import Client


class Command(BaseCommand):
    help = (
        "Wipe all clients (and cascaded claims, notes, documents, appointments) "
        "then seed 25 demo clients with varied claims."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Skip confirmation prompt (useful for CI).",
        )

    def handle(self, *args, **options):
        if not options["no_input"]:
            confirm = input(
                "This will DELETE all clients and related claims/appointments. Type YES to continue: "
            )
            if confirm.strip() != "YES":
                self.stdout.write(self.style.WARNING("Aborted."))
                return

        User = get_user_model()
        note_author = User.objects.filter(is_active=True).first()

        first_names = [
            "Maria",
            "James",
            "Susan",
            "David",
            "Lisa",
            "Robert",
            "Jennifer",
            "Michael",
            "Patricia",
            "William",
            "Linda",
            "Richard",
            "Barbara",
            "Joseph",
            "Elizabeth",
            "Thomas",
            "Nancy",
            "Charles",
            "Karen",
            "Christopher",
            "Betty",
            "Daniel",
            "Helen",
            "Matthew",
            "Sandra",
        ]
        last_names = [
            "Garcia",
            "Thompson",
            "Williams",
            "Martinez",
            "Johnson",
            "Brown",
            "Davis",
            "Miller",
            "Wilson",
            "Moore",
            "Taylor",
            "Anderson",
            "Thomas",
            "Jackson",
            "White",
            "Harris",
            "Martin",
            "Lee",
            "Walker",
            "Hall",
            "Allen",
            "Young",
            "King",
            "Wright",
            "Scott",
        ]
        streets = [
            "Maple St",
            "Oak Ave",
            "Pine Rd",
            "Cedar Ln",
            "Elm Dr",
            "Birch Way",
            "Willow Ct",
            "Magnolia Blvd",
            "Palm Dr",
            "Bay Shore Rd",
        ]
        cities = [
            ("Miami", "33101"),
            ("Fort Lauderdale", "33301"),
            ("Tampa", "33602"),
            ("Orlando", "32801"),
            ("Jacksonville", "32202"),
            ("St. Petersburg", "33701"),
            ("Tallahassee", "32301"),
            ("Naples", "34102"),
        ]
        insurers = [
            "State Farm",
            "Allstate",
            "Progressive",
            "USAA",
            "Liberty Mutual",
            "Travelers",
            "Nationwide",
            "Farmers Insurance",
            "Citizens Property Insurance",
            "Chubb",
            "Hanover",
            "American Family",
        ]
        loss_templates = [
            "Roof and interior water damage after storm.",
            "Kitchen fire; smoke damage throughout first floor.",
            "Burst pipe in crawl space; mold mitigation required.",
            "Wind-driven rain; siding and window seals compromised.",
            "Hail damage to roof shingles and gutters.",
            "Lightning strike; HVAC and electrical panel replacement.",
            "Tree limb impact; garage door and framing damage.",
            "Sewer backup; flooring and baseboards affected.",
        ]
        # 17 × 1 claim, 5 × 2, 2 × 3, 1 × 4 = 25 clients, 17+10+6+4 = 37 claims
        claim_counts = (
            [1] * 17
            + [2] * 5
            + [3] * 2
            + [4]
        )

        note_snippets = [
            "Initial inspection scheduled with insured.",
            "Carrier requested supplemental photos of roof decking.",
            "Insured prefers morning calls before 10am.",
            "Estimate sent to desk adjuster; awaiting response.",
            "Mitigation vendor on site; drying equipment in place.",
        ]

        with transaction.atomic():
            total_deleted, per_model = Client.objects.all().delete()
            self.stdout.write(
                self.style.NOTICE(
                    f"Cleared existing data ({total_deleted} objects deleted, including cascades): {per_model}"
                )
            )

            clients_created = 0
            claims_created = 0
            notes_created = 0

            base = date.today() - timedelta(days=400)

            for i in range(25):
                city, zipcode = cities[i % len(cities)]
                street_num = 100 + (i * 13) % 900
                notes_text = ""
                if i % 5 == 0:
                    notes_text = (
                        "Adjuster notes: insured works nights; best contact window is weekday afternoons."
                    )

                client = Client.objects.create(
                    first_name=first_names[i],
                    last_name=last_names[i],
                    phone=f"555-{2000 + i:04d}",
                    email=f"{first_names[i].lower()}.{last_names[i].lower()}{i}@example.com",
                    address=f"{street_num} {streets[i % len(streets)]}, {city}, FL {zipcode}",
                    notes=notes_text,
                )
                clients_created += 1

                n_claims = claim_counts[i]
                for j in range(n_claims):
                    loss_date = base + timedelta(days=i * 7 + j * 11 + (i + j) % 45)
                    claim = Claim(
                        client=client,
                        claim_number="",
                        status=[
                            Claim.STATUS_OPEN,
                            Claim.STATUS_UNDER_REVIEW,
                            Claim.STATUS_CLOSED,
                            Claim.STATUS_DENIED,
                        ][(i + j) % 4],
                        insurance_company=insurers[(i + j * 3) % len(insurers)],
                        description=loss_templates[(i + j) % len(loss_templates)],
                        date_of_loss=loss_date,
                    )
                    claim.save()
                    claims_created += 1

                    if note_author:
                        num_notes = 1 + (i + j) % 3
                        for k in range(num_notes):
                            ClaimNote.objects.create(
                                claim=claim,
                                created_by=note_author,
                                content=note_snippets[(i + j + k) % len(note_snippets)],
                            )
                            notes_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo seed complete: clients={clients_created}, claims={claims_created}, notes={notes_created}"
            )
        )
