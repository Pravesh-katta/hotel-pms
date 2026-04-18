from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required

from .forms import OTAConnectionForm
from .models import OTAConnection


@login_required
@role_required("hotel_admin")
def ota_list(request):
    connections = OTAConnection.objects.select_related("hotel")
    if request.hotel:
        connections = connections.filter(hotel=request.hotel)

    context = {"connections": connections}
    return render(request, "dashboard/settings/ota_list.html", context)


@login_required
@role_required("hotel_admin")
def ota_create(request):
    if request.method == "POST":
        form = OTAConnectionForm(request.POST)
        if form.is_valid():
            conn = form.save(commit=False)
            if request.hotel:
                conn.hotel = request.hotel
            conn.created_by = request.user
            conn.save()
            messages.success(request, f"OTA connection for {conn.get_channel_display()} created.")
            return redirect("ota_list")
    else:
        form = OTAConnectionForm()

    return render(request, "dashboard/settings/ota_form.html", {"form": form, "title": "Add OTA Connection"})


@login_required
@role_required("hotel_admin")
def ota_edit(request, pk):
    conn = get_object_or_404(OTAConnection, pk=pk)
    if request.hotel and conn.hotel != request.hotel:
        return HttpResponseForbidden()

    if request.method == "POST":
        form = OTAConnectionForm(request.POST, instance=conn)
        if form.is_valid():
            form.save()
            messages.success(request, "OTA connection updated.")
            return redirect("ota_list")
    else:
        form = OTAConnectionForm(instance=conn)

    return render(request, "dashboard/settings/ota_form.html", {"form": form, "title": f"Edit: {conn.get_channel_display()}"})
