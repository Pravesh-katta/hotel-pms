from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from apps.billing.models import Folio
from apps.reservations.models import Reservation
from apps.rooms.models import Room

from apps.accounts.models import HotelMembership

from .forms import HotelCreateForm
from .models import Hotel, HotelGroup


def _accessible_hotels(user):
    """Return queryset of hotels a user can access. Super_admin sees all."""
    profile = getattr(user, "staffprofile", None)
    if profile and profile.is_super_admin:
        return Hotel.objects.all()
    return Hotel.objects.filter(memberships__user=user, memberships__is_active=True).distinct()


@login_required
def group_dashboard(request):
    hotels = _accessible_hotels(request.user)

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "active")

    if status == "active":
        hotels = hotels.filter(is_active=True)
    elif status == "inactive":
        hotels = hotels.filter(is_active=False)

    if query:
        hotels = hotels.filter(
            Q(name__icontains=query) | Q(code__icontains=query) | Q(city__icontains=query)
        )

    hotels = hotels.order_by("name")

    context = {
        "hotels": hotels,
        "query": query,
        "status": status,
        "count": hotels.count(),
        "can_add_property": _can_add_property(request.user),
    }
    return render(request, "dashboard/group_dashboard.html", context)


def _user_group(user):
    """Infer the group this user belongs to (via any of their memberships or their staff profile)."""
    profile = getattr(user, "staffprofile", None)
    if profile and profile.hotel and profile.hotel.group_id:
        return profile.hotel.group
    membership = HotelMembership.objects.filter(user=user, is_active=True).select_related("hotel__group").first()
    if membership and membership.hotel.group_id:
        return membership.hotel.group
    return HotelGroup.objects.filter(slug="default").first()


def _can_add_property(user):
    profile = getattr(user, "staffprofile", None)
    if profile and profile.is_super_admin:
        return True
    return HotelMembership.objects.filter(user=user, role="hotel_admin", is_active=True).exists()


@login_required
def add_property(request):
    if not _can_add_property(request.user):
        messages.error(request, "You don't have permission to add a property.")
        return redirect("group_dashboard")

    group = _user_group(request.user)

    if request.method == "POST":
        form = HotelCreateForm(request.POST)
        if form.is_valid():
            hotel = form.save(commit=False)
            hotel.group = group
            hotel.save()
            HotelMembership.objects.create(user=request.user, hotel=hotel, role="hotel_admin")
            messages.success(request, f"Property “{hotel.name}” created.")
            return redirect("group_dashboard")
    else:
        form = HotelCreateForm()

    return render(request, "dashboard/add_property.html", {"form": form, "group": group})


@login_required
def select_hotel(request, hotel_id):
    hotel = get_object_or_404(_accessible_hotels(request.user), id=hotel_id)
    request.session["active_hotel_id"] = str(hotel.id)
    messages.success(request, f"Switched to {hotel.name}")
    return redirect("dashboard_home")


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
