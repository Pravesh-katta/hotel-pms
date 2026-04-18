from django.urls import path

from . import views

urlpatterns = [
    path("", views.housekeeping_board, name="housekeeping_board"),
    path("task/<int:pk>/update/", views.update_task_status, name="update_task_status"),
]
