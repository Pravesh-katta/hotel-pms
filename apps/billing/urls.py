from django.urls import path

from . import views

urlpatterns = [
    path("", views.folio_list, name="folio_list"),
    path("<int:pk>/", views.folio_detail, name="folio_detail"),
]
