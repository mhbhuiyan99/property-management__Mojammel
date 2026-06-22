from django.contrib.gis.db.models.functions import Distance
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Location, Property


def home(request):
    """Homepage with a search form (search box for a location/country name)."""
    locations = Location.objects.order_by("country")
    return render(request, "property_app/home.html", {"locations": locations})


def property_search(request):
    """
    Location-based property search + listing with pagination.
    Matches partially and case-insensitively against Location.country.
    """
    query = request.GET.get("location", "").strip()

    properties = Property.objects.select_related("location").prefetch_related("images")

    if query:
        properties = properties.filter(location__country__icontains=query)

    properties = properties.order_by("-created_at")

    paginator = Paginator(properties, 9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "property_app/property_list.html",
        {
            "page_obj": page_obj,
            "query": query,
            "result_count": paginator.count,
        },
    )


def property_detail(request, pk):
    """
    Property detail page with images, and distance from the location's
    center point (e.g. distance from the city center).
    """
    property_qs = Property.objects.select_related("location").prefetch_related("images")

    obj = get_object_or_404(property_qs, pk=pk)

    distance_km = None
    if obj.center and obj.location and obj.location.center:
        annotated = (
            Property.objects.filter(pk=obj.pk)
            .annotate(distance=Distance("center", obj.location.center))
            .first()
        )
        if annotated and annotated.distance is not None:
            distance_km = round(annotated.distance.km, 2)

    return render(
        request,
        "property_app/property_detail.html",
        {
            "property": obj,
            "distance_km": distance_km,
        },
    )