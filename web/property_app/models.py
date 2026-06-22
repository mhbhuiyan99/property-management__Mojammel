from django.contrib.gis.db import models
from pgvector.django import HnswIndex, VectorField

# all-MiniLM-L6-v2 (used in Day 3) outputs 384-dimension embeddings.
EMBEDDING_DIM = 384


class Location(models.Model):
    country = models.CharField(max_length=100)
    code = models.CharField(max_length=10, blank=True)
    center = models.PointField(geography=True, srid=4326, null=True, blank=True)
    embedding = VectorField(dimensions=EMBEDDING_DIM, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
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
        return self.country


class Property(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name="properties")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    center = models.PointField(geography=True, srid=4326, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "properties"

    def __str__(self):
        return self.name


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    url = models.URLField(blank=True)
    caption = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="properties/%Y/%m/", null=True, blank=True)

    def __str__(self):
        return self.caption or f"Image #{self.pk} for property {self.property_id}"
