from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from .forms import GuestForm
from .models import Guest


@login_required
def guest_list(request):
    guests = Guest.objects.select_related("hotel")
    if request.hotel:
        guests = guests.filter(hotel=request.hotel)

    q = request.GET.get("q", "")
    if q:
        guests = guests.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(phone__icontains=q)
            | Q(email__icontains=q)
        )

    nationality = request.GET.get("nationality", "")
    if nationality == "foreign":
        guests = guests.filter(is_foreign=True)
    elif nationality == "indian":
        guests = guests.filter(is_foreign=False)

    context = {"guests": guests[:100], "search_query": q, "nationality_filter": nationality}
    return render(request, "dashboard/guests/list.html", context)


@login_required
def guest_detail(request, pk):
    guest = get_object_or_404(Guest, pk=pk)
    if request.hotel and guest.hotel != request.hotel:
        return HttpResponseForbidden()

    reservations = guest.reservations.select_related("hotel").order_by("-check_in_date")[:10]
    context = {"guest": guest, "reservations": reservations}
    return render(request, "dashboard/guests/detail.html", context)


@login_required
def guest_create(request):
    if request.method == "POST":
        form = GuestForm(request.POST)
        if form.is_valid():
            guest = form.save(commit=False)
            if request.hotel:
                guest.hotel = request.hotel
            guest.save()
            return redirect("guest_detail", pk=guest.pk)
    else:
        form = GuestForm()

    return render(request, "dashboard/guests/form.html", {"form": form, "title": "Add Guest"})


@login_required
def guest_edit(request, pk):
    guest = get_object_or_404(Guest, pk=pk)
    if request.hotel and guest.hotel != request.hotel:
        return HttpResponseForbidden()

    if request.method == "POST":
        form = GuestForm(request.POST, instance=guest)
        if form.is_valid():
            form.save()
            return redirect("guest_detail", pk=guest.pk)
    else:
        form = GuestForm(instance=guest)

    return render(request, "dashboard/guests/form.html", {"form": form, "title": "Edit Guest"})
