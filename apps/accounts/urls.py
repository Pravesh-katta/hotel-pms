from django.urls import path

from .views import StaffLoginView, staff_logout

urlpatterns = [
    path("login/", StaffLoginView.as_view(), name="login"),
    path("logout/", staff_logout, name="logout"),
]
