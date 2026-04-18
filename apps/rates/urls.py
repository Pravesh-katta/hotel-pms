from django.urls import path

from . import views

urlpatterns = [
    path("", views.rate_plan_list, name="rate_plan_list"),
    path("create/", views.rate_plan_create, name="rate_plan_create"),
    path("<int:pk>/", views.rate_plan_edit, name="rate_plan_edit"),
    path("seasonal/<int:rate_plan_rate_pk>/", views.seasonal_rate_manage, name="seasonal_rate_manage"),
]
