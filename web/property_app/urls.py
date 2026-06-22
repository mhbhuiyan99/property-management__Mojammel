from django.urls import path

from . import views

app_name = "property_app"

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.property_search, name="property-search"),
    path("property/<int:pk>/", views.property_detail, name="property-detail"),
]

