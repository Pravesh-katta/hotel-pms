from django.urls import path

from . import views

urlpatterns = [
    path("", views.guest_list, name="guest_list"),
    path("create/", views.guest_create, name="guest_create"),
    path("<int:pk>/", views.guest_detail, name="guest_detail"),
    path("<int:pk>/edit/", views.guest_edit, name="guest_edit"),
]
