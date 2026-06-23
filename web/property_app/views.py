from django.contrib.gis.db.models.functions import Distance
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from pgvector.django import CosineDistance

from .embeddings import generate_embedding
from .models import Location, Property

# Cosine distance cutoff for "good enough" semantic matches (0 = identical
# meaning, 2 = opposite). Tune this if semantic search feels too loose/strict.
SEMANTIC_DISTANCE_THRESHOLD = 0.6
SEMANTIC_TOP_N = 5


def home(request):
    """Homepage with a search form (search box for a location/country name)."""
    locations = Location.objects.order_by("country")
    return render(request, "property_app/home.html", {"locations": locations})


def _semantic_location_ids(query):
    """
    Embeds the query and returns IDs of the nearest Locations by meaning,
    restricted to ones under the distance threshold.
    """
    query_embedding = generate_embedding(query)
    nearest = (
        Location.objects.exclude(embedding__isnull=True)
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:SEMANTIC_TOP_N]
    )
    return [loc.id for loc in nearest if loc.distance < SEMANTIC_DISTANCE_THRESHOLD]


def property_search(request):
    """
    Combined location search: first tries an exact/partial text match on
    Location.country. If that finds nothing, falls back to semantic
    (meaning-based) search over Location embeddings - so a query that
    doesn't literally appear in any location name can still surface
    relevant results.
    """
    query = request.GET.get("location", "").strip()

    properties = Property.objects.select_related("location").prefetch_related("images")
    used_semantic = False

    if query:
        text_match_ids = list(
            Location.objects.filter(country__icontains=query).values_list("id", flat=True)
        )
        if text_match_ids:
            properties = properties.filter(location_id__in=text_match_ids)
        else:
            semantic_ids = _semantic_location_ids(query)
            properties = properties.filter(location_id__in=semantic_ids)
            used_semantic = bool(semantic_ids)

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
            "used_semantic": used_semantic,
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
            "amenities": obj.amenities_list(),
            "distance_km": distance_km,
        },
    )


def location_autocomplete(request):
    """
    JSON autocomplete API powered by semantic search over Location
    embeddings. GET /api/locations/autocomplete/?q=<text>
    """
    query = request.GET.get("q", "").strip()
    if not query:
        return JsonResponse({"results": []})

    query_embedding = generate_embedding(query)
    nearest = (
        Location.objects.exclude(embedding__isnull=True)
        .annotate(distance=CosineDistance("embedding", query_embedding))
        .order_by("distance")[:8]
    )

    results = [
        {
            "id": loc.id,
            "country": loc.country,
            "code": loc.code,
            "score": round(1 - loc.distance, 4),
        }
        for loc in nearest
    ]
    return JsonResponse({"results": results})