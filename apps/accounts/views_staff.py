from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render

from .decorators import role_required
from .forms import StaffCreateForm
from .models import StaffProfile


@login_required
@role_required("hotel_admin")
def staff_list(request):
    profiles = StaffProfile.objects.select_related("user", "hotel")
    if request.hotel:
        profiles = profiles.filter(hotel=request.hotel)

    context = {"staff": profiles}
    return render(request, "dashboard/staff/list.html", context)


@login_required
@role_required("hotel_admin")
def staff_create(request):
    if request.method == "POST":
        form = StaffCreateForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
                first_name=form.cleaned_data["first_name"],
                last_name=form.cleaned_data["last_name"],
            )
            StaffProfile.objects.create(
                user=user,
                hotel=request.hotel,
                role=form.cleaned_data["role"],
                phone=form.cleaned_data["phone"],
            )
            messages.success(request, f"Staff member {user.get_full_name()} created.")
            return redirect("staff_list")
    else:
        form = StaffCreateForm()

    return render(request, "dashboard/staff/form.html", {"form": form, "title": "Add Staff"})


@login_required
@role_required("hotel_admin")
def staff_toggle_active(request, pk):
    profile = get_object_or_404(StaffProfile, pk=pk)
    if request.hotel and profile.hotel != request.hotel:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    if request.method == "POST":
        profile.user.is_active = not profile.user.is_active
        profile.user.save(update_fields=["is_active"])
        action = "activated" if profile.user.is_active else "deactivated"
        messages.success(request, f"{profile.user.get_full_name()} {action}.")

    return redirect("staff_list")
