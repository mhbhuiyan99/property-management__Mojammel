from django.contrib.gis.db import models
from pgvector.django import HnswIndex, VectorField

EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output size, used in Day 3


class Location(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="Country / location name")
    code = models.CharField(max_length=10, blank=True, help_text="Country code, e.g. US, BD")
    center = models.PointField(geography=True, srid=4326, null=True, blank=True)
    embedding = VectorField(dimensions=EMBEDDING_DIM, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            HnswIndex(
                name="location_embedding_hnsw_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]

    def __str__(self):
        return self.name


class Property(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="properties")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    center = models.PointField(geography=True, srid=4326, null=True, blank=True)

    property_type = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bedrooms = models.PositiveSmallIntegerField(default=0)
    bathrooms = models.PositiveSmallIntegerField(default=0)
    amenities = models.TextField(blank=True, help_text="Comma-separated amenities")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "properties"

    def __str__(self):
        return self.name

    def amenities_list(self):
        return [a.strip() for a in self.amenities.split(",") if a.strip()]


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    url = models.URLField(blank=True, help_text="Source image URL (e.g. from CSV import)")
    caption = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="properties/%Y/%m/", null=True, blank=True)

    def __str__(self):
        return self.caption or f"Image #{self.pk} for {self.property_id}"

