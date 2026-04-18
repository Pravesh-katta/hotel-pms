from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.guests.models import Guest

from .forms import ReservationCreateForm, ReservationEditForm, WalkInForm
from .models import Reservation
from .services import create_reservation, modify_reservation
from .state_machine import InvalidTransition
from .workflows import perform_cancellation, perform_check_in, perform_check_out, perform_walk_in


@login_required
def reservation_list(request):
    qs = Reservation.objects.select_related("guest", "hotel").order_by("-created_at")
    if request.hotel:
        qs = qs.filter(hotel=request.hotel)

    status = request.GET.get("status", "")
    source = request.GET.get("source", "")
    q = request.GET.get("q", "")

    if status:
        qs = qs.filter(status=status)
    if source:
        qs = qs.filter(source=source)
    if q:
        qs = qs.filter(
            Q(confirmation_number__icontains=q)
            | Q(guest__first_name__icontains=q)
            | Q(guest__last_name__icontains=q)
            | Q(guest__phone__icontains=q)
        )

    context = {
        "reservations": qs[:100],
        "status_choices": Reservation.STATUS_CHOICES,
        "source_choices": Reservation.SOURCE_CHOICES,
        "current_status": status,
        "current_source": source,
        "search_query": q,
    }
    return render(request, "dashboard/reservations/list.html", context)


@login_required
def reservation_detail(request, pk):
    reservation = get_object_or_404(
        Reservation.objects.select_related("guest", "hotel"), pk=pk
    )
    if request.hotel and reservation.hotel != request.hotel:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    res_rooms = reservation.rooms.select_related("room", "room_type").prefetch_related("nightly_rates")
    folio = getattr(reservation, "folio", None)
    charges = folio.charges.all() if folio else []
    verifications = reservation.verifications.all()

    context = {
        "reservation": reservation,
        "res_rooms": res_rooms,
        "folio": folio,
        "charges": charges,
        "verifications": verifications,
    }
    return render(request, "dashboard/reservations/detail.html", context)


@login_required
def reservation_create(request):
    hotel = request.hotel
    if request.method == "POST":
        form = ReservationCreateForm(hotel, request.POST)
        if form.is_valid():
            try:
                reservation = create_reservation(
                    hotel=hotel or form.cleaned_data["room"].hotel,
                    guest=form.cleaned_data["guest"],
                    room=form.cleaned_data["room"],
                    room_type=form.cleaned_data["room_type"],
                    check_in_date=form.cleaned_data["check_in_date"],
                    check_out_date=form.cleaned_data["check_out_date"],
                    source=form.cleaned_data["source"],
                    num_adults=form.cleaned_data["num_adults"],
                    num_children=form.cleaned_data["num_children"],
                    special_requests=form.cleaned_data["special_requests"],
                    created_by=request.user,
                )
                messages.success(request, f"Reservation #{reservation.confirmation_number} created.")
                return redirect("reservation_detail", pk=reservation.pk)
            except ValueError as e:
                messages.error(request, str(e))
    else:
        initial = {}
        if request.GET.get("room"):
            initial["room"] = request.GET["room"]
        if request.GET.get("room_type"):
            initial["room_type"] = request.GET["room_type"]
        if request.GET.get("check_in"):
            initial["check_in_date"] = request.GET["check_in"]
        form = ReservationCreateForm(hotel, initial=initial)

    return render(request, "dashboard/reservations/create.html", {"form": form})


@login_required
def walk_in(request):
    hotel = request.hotel
    if request.method == "POST":
        form = WalkInForm(hotel, request.POST)
        if form.is_valid():
            try:
                # Create or find guest
                guest, _ = Guest.objects.get_or_create(
                    hotel=hotel,
                    phone=form.cleaned_data["phone"],
                    defaults={
                        "first_name": form.cleaned_data["first_name"],
                        "last_name": form.cleaned_data["last_name"],
                        "id_type": form.cleaned_data.get("id_type", ""),
                        "id_number": form.cleaned_data.get("id_number", ""),
                        "nationality": form.cleaned_data.get("nationality", "Indian"),
                    },
                )

                room = form.cleaned_data["room"]
                reservation = perform_walk_in(
                    hotel=hotel,
                    guest=guest,
                    room=room,
                    room_type=room.room_type,
                    nights=form.cleaned_data["nights"],
                    staff_user=request.user,
                )
                messages.success(
                    request,
                    f"Walk-in #{reservation.confirmation_number} — Guest checked in to Room {room.room_number}."
                )
                return redirect("reservation_detail", pk=reservation.pk)
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = WalkInForm(hotel)

    return render(request, "dashboard/reservations/walk_in.html", {"form": form})


@login_required
def check_in(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.hotel and reservation.hotel != request.hotel:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    if request.method == "POST":
        try:
            perform_check_in(reservation, request.user)
            messages.success(request, f"Guest checked in — #{reservation.confirmation_number}")
        except InvalidTransition as e:
            messages.error(request, str(e))
        return redirect("reservation_detail", pk=pk)

    return render(request, "dashboard/reservations/check_in.html", {"reservation": reservation})


@login_required
def check_out(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.hotel and reservation.hotel != request.hotel:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    folio = getattr(reservation, "folio", None)
    if request.method == "POST":
        try:
            perform_check_out(reservation, request.user)
            messages.success(request, f"Guest checked out — #{reservation.confirmation_number}")
        except InvalidTransition as e:
            messages.error(request, str(e))
        return redirect("reservation_detail", pk=pk)

    return render(request, "dashboard/reservations/check_out.html", {
        "reservation": reservation,
        "folio": folio,
    })


@login_required
def reservation_cancel(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    if request.hotel and reservation.hotel != request.hotel:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    if request.method == "POST":
        try:
            perform_cancellation(reservation, request.user)
            messages.success(request, f"Reservation #{reservation.confirmation_number} cancelled.")
        except InvalidTransition as e:
            messages.error(request, str(e))
        return redirect("reservation_detail", pk=pk)

    return render(request, "dashboard/reservations/cancel.html", {"reservation": reservation})


@login_required
def reservation_edit(request, pk):
    reservation = get_object_or_404(
        Reservation.objects.select_related("guest", "hotel"), pk=pk
    )
    if request.hotel and reservation.hotel != request.hotel:
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden()

    if reservation.status not in ("confirmed", "checked_in"):
        messages.error(request, "Can only edit confirmed or checked-in reservations.")
        return redirect("reservation_detail", pk=pk)

    res_room = reservation.rooms.select_related("room", "room_type").first()

    if request.method == "POST":
        form = ReservationEditForm(reservation, request.POST)
        if form.is_valid():
            try:
                new_room = form.cleaned_data["room"]
                room_changed = res_room and new_room.pk != res_room.room_id

                modify_reservation(
                    reservation=reservation,
                    new_check_out=form.cleaned_data["check_out_date"],
                    new_room=new_room if room_changed else None,
                    num_adults=form.cleaned_data["num_adults"],
                    num_children=form.cleaned_data["num_children"],
                    special_requests=form.cleaned_data["special_requests"],
                    modified_by=request.user,
                )
                messages.success(request, f"Reservation #{reservation.confirmation_number} updated.")
                return redirect("reservation_detail", pk=pk)
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = ReservationEditForm(reservation)

    context = {
        "form": form,
        "reservation": reservation,
        "res_room": res_room,
    }
    return render(request, "dashboard/reservations/edit.html", context)
