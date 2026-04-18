from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import render

from apps.billing.models import Folio
from apps.reservations.models import Reservation
from apps.rooms.models import Room


@login_required
def dashboard_home(request):
    hotel = request.hotel
    today = date.today()

    if hotel:
        rooms = Room.objects.filter(hotel=hotel, is_active=True)
        reservations = Reservation.objects.filter(hotel=hotel)
    else:
        rooms = Room.objects.filter(is_active=True)
        reservations = Reservation.objects.all()

    total_rooms = rooms.count()
    occupied = rooms.filter(status="occupied").count()
    available = rooms.filter(status="available").count()
    dirty = rooms.filter(status="dirty").count()

    arrivals_today = reservations.filter(
        check_in_date=today, status="confirmed"
    ).count()
    departures_today = reservations.filter(
        check_out_date=today, status="checked_in"
    ).count()

    if hotel:
        pending_balance = Folio.objects.filter(
            hotel=hotel, status="open", balance__gt=0
        ).aggregate(total=Sum("balance"))["total"] or 0
    else:
        pending_balance = Folio.objects.filter(
            status="open", balance__gt=0
        ).aggregate(total=Sum("balance"))["total"] or 0

    occupancy_pct = round((occupied / total_rooms * 100), 1) if total_rooms > 0 else 0

    context = {
        "today": today,
        "total_rooms": total_rooms,
        "occupied": occupied,
        "available": available,
        "dirty": dirty,
        "arrivals_today": arrivals_today,
        "departures_today": departures_today,
        "pending_balance": pending_balance,
        "occupancy_pct": occupancy_pct,
    }
    return render(request, "dashboard/index.html", context)
