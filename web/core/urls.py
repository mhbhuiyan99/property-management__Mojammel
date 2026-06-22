from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path


def health_check(request):
    return HttpResponse("Property Management System is running.")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", health_check, name="health-check"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

