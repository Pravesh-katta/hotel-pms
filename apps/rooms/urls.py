from django.urls import path

from . import views

urlpatterns = [
    path("", views.room_list, name="room_list"),
    path("status-board/", views.room_status_board, name="room_status_board"),
    path("<int:pk>/update-status/", views.update_room_status, name="update_room_status"),
]
