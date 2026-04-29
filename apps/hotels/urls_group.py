from django.urls import path

from .views import add_property, group_dashboard, select_hotel

urlpatterns = [
    path("", group_dashboard, name="group_dashboard"),
    path("new/", add_property, name="add_property"),
    path("select/<uuid:hotel_id>/", select_hotel, name="select_hotel"),
]
