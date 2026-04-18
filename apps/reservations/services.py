from datetime import timedelta

from django.db import transaction

from apps.billing.services import create_folio, post_all_room_charges
from apps.rates.services import get_rates_for_stay
from apps.rooms.availability import is_room_available

from .models import Reservation, ReservationRoom, RoomNightRate


def generate_confirmation_number(hotel):
    """Generate next confirmation number for the hotel."""
    last = Reservation.objects.filter(hotel=hotel).order_by("-created_at").first()
    if last and last.confirmation_number:
        try:
            num = int(last.confirmation_number.split("-")[1]) + 1
        except (IndexError, ValueError):
            num = 1001
    else:
        num = 1001
    return f"BK-{num:04d}"


@transaction.atomic
def create_reservation(
    hotel, guest, room, room_type, check_in_date, check_out_date,
    source="walk_in", num_adults=1, num_children=0,
    special_requests="", created_by=None, rate_plan=None,
):
    """
    Create a complete reservation with room assignment, nightly rates, and folio.
    """
    # Validate availability
    if not is_room_available(room, check_in_date, check_out_date):
        raise ValueError(f"Room {room.room_number} is not available for these dates.")

    # Create reservation
    confirmation_number = generate_confirmation_number(hotel)
    reservation = Reservation.objects.create(
        hotel=hotel,
        confirmation_number=confirmation_number,
        guest=guest,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        status="confirmed",
        source=source,
        num_adults=num_adults,
        num_children=num_children,
        special_requests=special_requests,
        created_by=created_by,
    )

    # Create room assignment
    res_room = ReservationRoom.objects.create(
        reservation=reservation,
        room=room,
        room_type=room_type,
        rate_plan=rate_plan,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
    )

    # Calculate and store nightly rates
    nightly_rates = get_rates_for_stay(hotel, room_type, check_in_date, check_out_date, source)
    for night_date, rate in nightly_rates:
        RoomNightRate.objects.create(
            reservation_room=res_room,
            date=night_date,
            rate=rate,
        )

    # Create folio and post charges
    folio = create_folio(reservation)
    post_all_room_charges(folio, created_by)

    return reservation


@transaction.atomic
def modify_reservation(reservation, new_check_out, new_room=None,
                       num_adults=None, num_children=None,
                       special_requests=None, modified_by=None):
    """
    Modify an existing reservation:
    - Extend or shorten stay (change check_out_date)
    - Change room assignment
    - Update guest count / special requests
    Recalculates nightly rates and folio charges for added/removed nights.
    """
    if reservation.status not in ("confirmed", "checked_in"):
        raise ValueError("Can only modify confirmed or checked-in reservations.")

    old_check_out = reservation.check_out_date
    res_room = reservation.rooms.first()
    if not res_room:
        raise ValueError("No room assignment found.")

    room = new_room or res_room.room
    room_type = room.room_type

    # Validate new dates
    if new_check_out <= reservation.check_in_date:
        raise ValueError("Check-out must be after check-in.")

    # If room is changing, check availability for the new room
    if new_room and new_room != res_room.room:
        if not is_room_available(new_room, reservation.check_in_date, new_check_out,
                                  exclude_reservation=reservation):
            raise ValueError(f"Room {new_room.room_number} is not available for these dates.")

        # Update old room status if guest was checked in
        if reservation.status == "checked_in":
            old_room = res_room.room
            old_room.status = "dirty"
            old_room.save(update_fields=["status"])
            new_room.status = "occupied"
            new_room.save(update_fields=["status"])

        res_room.room = new_room
        res_room.room_type = room_type

    # If extending stay, check the current room is available for extended dates
    if new_check_out > old_check_out and new_room is None:
        from apps.reservations.models import ReservationRoom as RR
        conflicts = RR.objects.filter(
            room=res_room.room,
            reservation__status__in=["confirmed", "checked_in"],
            check_in_date__lt=new_check_out,
            check_out_date__gt=old_check_out,
        ).exclude(reservation=reservation).exists()
        if conflicts:
            raise ValueError(f"Room {res_room.room.room_number} is booked after {old_check_out}. Cannot extend.")

    # Update reservation fields
    reservation.check_out_date = new_check_out
    if num_adults is not None:
        reservation.num_adults = num_adults
    if num_children is not None:
        reservation.num_children = num_children
    if special_requests is not None:
        reservation.special_requests = special_requests
    reservation.save()

    # Update ReservationRoom dates
    res_room.check_out_date = new_check_out
    res_room.save()

    # Handle nightly rates for date changes
    if new_check_out > old_check_out:
        # Extending — add nightly rates for new nights
        new_rates = get_rates_for_stay(
            reservation.hotel, room_type, old_check_out, new_check_out, reservation.source
        )
        for night_date, rate in new_rates:
            RoomNightRate.objects.get_or_create(
                reservation_room=res_room,
                date=night_date,
                defaults={"rate": rate},
            )
        # Post charges for new nights
        folio = reservation.folio
        for night_date, rate in new_rates:
            from apps.billing.services import post_room_charges
            post_room_charges(folio, res_room, night_date, modified_by)

    elif new_check_out < old_check_out:
        # Shortening — remove nightly rates for removed nights and void their charges
        removed_rates = RoomNightRate.objects.filter(
            reservation_room=res_room,
            date__gte=new_check_out,
        )
        removed_dates = list(removed_rates.values_list("date", flat=True))
        removed_rates.delete()

        # Remove charges for those dates
        from apps.billing.models import FolioCharge
        folio = reservation.folio
        FolioCharge.objects.filter(
            folio=folio,
            charge_date__in=removed_dates,
        ).delete()
        folio.recalculate()

    return reservation
