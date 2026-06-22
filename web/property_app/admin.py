from django.contrib import admin
from django.utils.html import format_html

from .models import Location, Property, PropertyImage


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ("image", "url", "caption", "preview")
    readonly_fields = ("preview",)

    def preview(self, obj):
        src = obj.image.url if obj.image else obj.url
        if not src:
            return "(no image yet)"
        return format_html(
            '<img src="{}" style="height:80px;border-radius:4px;object-fit:cover;" />',
            src,
        )

    preview.short_description = "Preview"

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("country", "code", "center", "created_at")
    list_filter = ("code",)
    search_fields = ("country", "code")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "bedrooms", "bathrooms", "primary_image_preview", "created_at")
    list_filter = ("location", "bedrooms", "bathrooms")
    search_fields = ("name", "description", "location__country")
    inlines = [PropertyImageInline]
    readonly_fields = ("created_at", "updated_at")

    def primary_image_preview(self, obj):
        first_image = obj.images.first()
        if not first_image:
            return "(no image)"
        src = first_image.image.url if first_image.image else first_image.url
        if not src:
            return "(no image)"
        return format_html(
            '<img src="{}" style="height:50px;border-radius:4px;object-fit:cover;" />',
            src,
        )

    primary_image_preview.short_description = "Image"