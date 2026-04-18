from django.urls import path

from .views_settings import ota_create, ota_edit, ota_list

urlpatterns = [
    path("", ota_list, name="ota_list"),
    path("create/", ota_create, name="ota_create"),
    path("<int:pk>/", ota_edit, name="ota_edit"),
]
