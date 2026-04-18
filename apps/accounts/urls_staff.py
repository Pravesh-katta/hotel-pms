from django.urls import path

from .views_staff import staff_create, staff_list, staff_toggle_active

urlpatterns = [
    path("", staff_list, name="staff_list"),
    path("create/", staff_create, name="staff_create"),
    path("<int:pk>/toggle/", staff_toggle_active, name="staff_toggle_active"),
]
