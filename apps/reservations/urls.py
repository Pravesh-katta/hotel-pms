from django.urls import path

from . import views

urlpatterns = [
    path("", views.reservation_list, name="reservation_list"),
    path("create/", views.reservation_create, name="reservation_create"),
    path("walk-in/", views.walk_in, name="walk_in"),
    path("<int:pk>/", views.reservation_detail, name="reservation_detail"),
    path("<int:pk>/edit/", views.reservation_edit, name="reservation_edit"),
    path("<int:pk>/check-in/", views.check_in, name="check_in"),
    path("<int:pk>/check-out/", views.check_out, name="check_out"),
    path("<int:pk>/cancel/", views.reservation_cancel, name="reservation_cancel"),
]
