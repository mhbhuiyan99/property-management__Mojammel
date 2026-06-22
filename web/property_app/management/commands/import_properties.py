import pandas as pd
from django.conf import settings
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand

from property_app.models import Location, Property, PropertyImage


class Command(BaseCommand):
    help = "Import vacation rental properties from a CSV file using pandas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            type=str,
            default=str(settings.BASE_DIR / "data" / "properties.csv"),
            help="Path to the CSV file to import.",
        )

    def handle(self, *args, **options):
        csv_path = options["csv"]
        self.stdout.write(f"Reading CSV: {csv_path}")

        df = pd.read_csv(csv_path)
        required_cols = {
            "country", "country_code", "location_lat", "location_lng",
            "property_name", "description", "property_lat", "property_lng",
            "image_urls",
        }
        missing = required_cols - set(df.columns)
        if missing:
            self.stderr.write(self.style.ERROR(f"CSV is missing columns: {missing}"))
            return

        created_locations = 0
        created_properties = 0
        created_images = 0

        for _, row in df.iterrows():
            location, loc_created = Location.objects.get_or_create(
                country=str(row["country"]).strip(),
                defaults={
                    "code": str(row.get("country_code", "")).strip(),
                    "center": Point(float(row["location_lng"]), float(row["location_lat"])),
                },
            )
            if loc_created:
                created_locations += 1

            prop, prop_created = Property.objects.get_or_create(
                name=str(row["property_name"]).strip(),
                location=location,
                defaults={
                    "description": str(row.get("description", "") or ""),
                    "center": (
                        Point(float(row["property_lng"]), float(row["property_lat"]))
                        if pd.notna(row.get("property_lng")) and pd.notna(row.get("property_lat"))
                        else None
                    ),
                },
            )
            if prop_created:
                created_properties += 1

            image_urls = str(row.get("image_urls", "") or "")
            if prop_created:
                for url in [u.strip() for u in image_urls.split(",") if u.strip()]:
                    PropertyImage.objects.create(property=prop, url=url)
                    created_images += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Locations created: {created_locations}, "
            f"Properties created: {created_properties}, "
            f"Images created: {created_images}."
        ))