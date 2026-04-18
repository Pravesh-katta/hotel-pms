from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render

from apps.guests.models import Guest
from apps.reservations.models import Reservation
from apps.rooms.models import Room


@login_required
def global_search(request):
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return HttpResponse("")

    hotel = request.hotel

    # Search guests
    guests = Guest.objects.filter(
        Q(first_name__icontains=q)
        | Q(last_name__icontains=q)
        | Q(phone__icontains=q)
        | Q(email__icontains=q)
    )
    if hotel:
        guests = guests.filter(hotel=hotel)
    guests = guests[:5]

    # Search reservations
    reservations = Reservation.objects.filter(
        Q(confirmation_number__icontains=q)
        | Q(external_booking_id__icontains=q)
        | Q(guest__first_name__icontains=q)
        | Q(guest__last_name__icontains=q)
        | Q(guest__phone__icontains=q)
    ).select_related("guest")
    if hotel:
        reservations = reservations.filter(hotel=hotel)
    reservations = reservations[:5]

    # Search rooms
    rooms = Room.objects.filter(room_number__icontains=q)
    if hotel:
        rooms = rooms.filter(hotel=hotel)
    rooms = rooms[:5]

    context = {
        "guests": guests,
        "reservations": reservations,
        "rooms": rooms,
        "query": q,
    }
    return render(request, "dashboard/components/search_results.html", context)
