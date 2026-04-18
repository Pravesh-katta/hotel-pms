from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.reservations.models import ReservationRoom

from .models import Room


@login_required
def calendar_grid(request):
    """Room grid calendar: rooms (rows) x dates (columns)."""
    hotel = request.hotel

    start_str = request.GET.get("start", "")
    try:
        start_date = date.fromisoformat(start_str)
    except (ValueError, TypeError):
        start_date = date.today()

    days = int(request.GET.get("days", 14))
    days = min(days, 30)
    end_date = start_date + timedelta(days=days)
    dates = [start_date + timedelta(days=i) for i in range(days)]

    # Get rooms
    rooms = Room.objects.filter(is_active=True).select_related("room_type")
    if hotel:
        rooms = rooms.filter(hotel=hotel)
    rooms = rooms.order_by("room_number")

    # Get all reservations overlapping this date range
    res_rooms = ReservationRoom.objects.filter(
        reservation__status__in=["confirmed", "checked_in"],
        check_in_date__lt=end_date,
        check_out_date__gt=start_date,
    ).select_related("reservation", "reservation__guest", "room")
    if hotel:
        res_rooms = res_rooms.filter(reservation__hotel=hotel)

    # Build lookup: room_id -> list of ReservationRoom
    room_bookings = {}
    for rr in res_rooms:
        room_bookings.setdefault(rr.room_id, []).append(rr)

    # Build grid — each cell is rendered individually, no colspan tricks
    grid = []
    for room in rooms:
        row = {"room": room, "cells": []}
        bookings = room_bookings.get(room.pk, [])

        for d in dates:
            booking = None
            for rr in bookings:
                if rr.check_in_date <= d < rr.check_out_date:
                    booking = rr
                    break

            # Determine if this is the first visible cell of the booking
            is_first_visible = False
            if booking:
                visible_start = max(booking.check_in_date, start_date)
                is_first_visible = (d == visible_start)

            row["cells"].append({
                "date": d,
                "booking": booking,
                "is_first_visible": is_first_visible,
                "is_booked": booking is not None,
            })
        grid.append(row)

    # Generate month links for a full year (2 months back + 12 months forward)
    today = date.today()
    month_links = []
    for offset in range(-2, 13):
        m = today.month + offset
        y = today.year
        while m < 1:
            m += 12
            y -= 1
        while m > 12:
            m -= 12
            y += 1
        first_of_month = date(y, m, 1)
        month_links.append({
            "date": first_of_month,
            "label": first_of_month.strftime("%b %Y"),
            "is_current": (start_date.year == y and start_date.month == m),
        })

    context = {
        "grid": grid,
        "dates": dates,
        "start_date": start_date,
        "end_date": end_date,
        "days": days,
        "prev_start": (start_date - timedelta(days=days)).isoformat(),
        "next_start": (start_date + timedelta(days=days)).isoformat(),
        "today": today,
        "month_links": month_links,
    }
    return render(request, "dashboard/reservations/calendar.html", context)


@login_required
def calendar_monthly(request):
    """Monthly overview: occupancy stats per day."""
    hotel = request.hotel

    month_str = request.GET.get("month", "")
    try:
        year, month = map(int, month_str.split("-"))
        first_day = date(year, month, 1)
    except (ValueError, TypeError):
        first_day = date.today().replace(day=1)

    if first_day.month == 12:
        last_day = date(first_day.year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(first_day.year, first_day.month + 1, 1) - timedelta(days=1)

    days_in_month = (last_day - first_day).days + 1
    dates = [first_day + timedelta(days=i) for i in range(days_in_month)]

    rooms = Room.objects.filter(is_active=True)
    if hotel:
        rooms = rooms.filter(hotel=hotel)
    total_rooms = rooms.count()

    res_rooms = list(ReservationRoom.objects.filter(
        reservation__status__in=["confirmed", "checked_in", "checked_out"],
        check_in_date__lt=last_day + timedelta(days=1),
        check_out_date__gt=first_day,
    ).select_related("reservation"))
    if hotel:
        res_rooms = [rr for rr in res_rooms if rr.reservation.hotel_id == hotel.pk]

    day_stats = []
    for d in dates:
        occupied = sum(1 for rr in res_rooms if rr.check_in_date <= d < rr.check_out_date)
        occ_pct = round(occupied / total_rooms * 100) if total_rooms else 0
        arrivals = sum(1 for rr in res_rooms if rr.check_in_date == d)
        departures = sum(1 for rr in res_rooms if rr.check_out_date == d)

        day_stats.append({
            "date": d,
            "occupied": occupied,
            "total": total_rooms,
            "occupancy_pct": occ_pct,
            "arrivals": arrivals,
            "departures": departures,
        })

    prev_month = (first_day - timedelta(days=1)).replace(day=1)
    if first_day.month == 12:
        next_month = date(first_day.year + 1, 1, 1)
    else:
        next_month = date(first_day.year, first_day.month + 1, 1)

    context = {
        "day_stats": day_stats,
        "month_name": first_day.strftime("%B %Y"),
        "current_month_value": first_day.strftime("%Y-%m"),
        "prev_month": prev_month.strftime("%Y-%m"),
        "next_month": next_month.strftime("%Y-%m"),
        "today": date.today(),
    }
    return render(request, "dashboard/reservations/calendar_monthly.html", context)
