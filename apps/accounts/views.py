from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect


class StaffLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True


def staff_logout(request):
    logout(request)
    return redirect("login")
