from django.urls import path

from .calendar_views import calendar_grid, calendar_monthly

urlpatterns = [
    path("", calendar_grid, name="calendar_grid"),
    path("monthly/", calendar_monthly, name="calendar_monthly"),
]
