from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from apps.audit.models import DailyAuditSnapshot
from apps.hotels.models import Hotel
from apps.reservations.models import Reservation
from apps.rooms.models import Room

from .models import Folio, FolioCharge
from .services import get_gst_rate, post_room_charges


def run_night_audit(hotel, audit_date=None):
    """
    Run the night audit for a specific hotel.

    Steps:
    1. Post room charges for all checked-in guests
    2. Handle no-shows
    3. Flag overdue checkouts
    4. Recalculate all open folios
    5. Create daily audit snapshot

    Idempotent: safe to re-run.
    """
    if audit_date is None:
        audit_date = date.today()

    result = {
        "hotel": hotel.code,
        "audit_date": str(audit_date),
        "charges_posted": 0,
        "noshow_count": 0,
        "overdue_count": 0,
        "errors": [],
    }

    # Step 1: Post room charges for checked-in reservations
    checked_in = Reservation.objects.filter(
        hotel=hotel,
        status="checked_in",
    )

    for reservation in checked_in:
        try:
            folio = reservation.folio
            for res_room in reservation.rooms.all():
                # Only post if this date is within the stay
                if res_room.check_in_date <= audit_date < res_room.check_out_date:
                    post_room_charges(folio, res_room, audit_date)
                    result["charges_posted"] += 1
        except Folio.DoesNotExist:
            result["errors"].append(f"No folio for reservation {reservation.confirmation_number}")
        except Exception as e:
            result["errors"].append(f"Error posting charges for {reservation.confirmation_number}: {e}")

    # Step 2: Handle no-shows
    # Reservations confirmed for today that were not checked in
    no_shows = Reservation.objects.filter(
        hotel=hotel,
        status="confirmed",
        check_in_date=audit_date,
    )

    for reservation in no_shows:
        try:
            from apps.reservations.state_machine import transition_reservation
            transition_reservation(reservation, "no_show")

            # Post no-show fee
            res_room = reservation.rooms.first()
            if res_room:
                first_night = res_room.nightly_rates.order_by("date").first()
                if first_night:
                    try:
                        folio = reservation.folio
                    except Folio.DoesNotExist:
                        from .services import create_folio
                        folio = create_folio(reservation)

                    FolioCharge.objects.create(
                        folio=folio,
                        charge_type="no_show_fee",
                        description=f"No-show fee — Room {res_room.room.room_number}",
                        amount=first_night.rate,
                        charge_date=audit_date,
                    )
                    folio.recalculate()

            # Release room
            if res_room:
                room = res_room.room
                if room.status != "occupied":
                    pass  # room wasn't occupied yet

            result["noshow_count"] += 1
        except Exception as e:
            result["errors"].append(f"No-show error for {reservation.confirmation_number}: {e}")

    # Step 3: Flag overdue checkouts
    tomorrow = audit_date + timedelta(days=1)
    overdue = Reservation.objects.filter(
        hotel=hotel,
        status="checked_in",
        check_out_date__lte=audit_date,
    )
    result["overdue_count"] = overdue.count()

    # Step 4: Recalculate all open folios
    open_folios = Folio.objects.filter(hotel=hotel, status="open")
    for folio in open_folios:
        try:
            folio.recalculate()
        except Exception:
            pass

    # Step 5: Create daily audit snapshot
    total_rooms = Room.objects.filter(hotel=hotel, is_active=True).count()
    occupied_rooms = Room.objects.filter(hotel=hotel, is_active=True, status="occupied").count()
    occupancy_pct = round(occupied_rooms / total_rooms * 100, 2) if total_rooms else 0

    total_outstanding = sum(f.balance for f in Folio.objects.filter(hotel=hotel, status="open", balance__gt=0))

    revenue_posted = sum(
        c.amount for c in FolioCharge.objects.filter(
            folio__hotel=hotel,
            charge_date=audit_date,
            charge_type__in=["room_charge", "cgst", "sgst"],
        )
    )

    arrivals_tomorrow = Reservation.objects.filter(
        hotel=hotel, check_in_date=tomorrow, status="confirmed"
    ).count()
    departures_tomorrow = Reservation.objects.filter(
        hotel=hotel, check_out_date=tomorrow, status="checked_in"
    ).count()

    DailyAuditSnapshot.objects.update_or_create(
        hotel=hotel,
        audit_date=audit_date,
        defaults={
            "total_rooms": total_rooms,
            "occupied_rooms": occupied_rooms,
            "occupancy_percent": occupancy_pct,
            "revenue_posted": revenue_posted,
            "total_outstanding": total_outstanding,
            "noshow_count": result["noshow_count"],
            "arrivals_tomorrow": arrivals_tomorrow,
            "departures_tomorrow": departures_tomorrow,
            "audit_status": "completed" if not result["errors"] else "partial",
            "error_message": "\n".join(result["errors"]),
            "completed_at": timezone.now(),
        },
    )

    return result


def run_night_audit_all_hotels(audit_date=None):
    """Run night audit for all active hotels."""
    results = []
    for hotel in Hotel.objects.filter(is_active=True):
        try:
            result = run_night_audit(hotel, audit_date)
            results.append(result)
        except Exception as e:
            results.append({"hotel": hotel.code, "error": str(e)})
    return results
