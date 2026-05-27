from django.core.management.base import BaseCommand

from ingestion.models import Facility, Organization


class Command(BaseCommand):
    help = "Seed demo tenant and facility lookup data."

    def handle(self, *args, **options):
        org, _ = Organization.objects.get_or_create(name="Breathe Demo Client", slug="breathe-demo")
        facilities = [
            ("BLR01", "Bengaluru Manufacturing Plant", "IN", {"sap_plant": "BLR01", "meter": "MTR-BLR-01"}),
            ("PNQ02", "Pune Distribution Centre", "IN", {"sap_plant": "PNQ02"}),
        ]
        for code, name, country, metadata in facilities:
            Facility.objects.update_or_create(
                organization=org,
                code=code,
                defaults={"name": name, "country": country, "metadata": metadata},
            )
        self.stdout.write(self.style.SUCCESS("Seeded demo organization and facilities."))

