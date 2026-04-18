from datetime import date
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.billing.models import FolioCharge
from apps.billing.services import create_folio, post_all_room_charges
from apps.guests.models import GuestVerification
from apps.housekeeping.models import HousekeepingTask
from apps.rooms.models import Room

from .services import create_reservation
from .state_machine import transition_reservation


@transaction.atomic
def perform_check_in(reservation, staff_user):
    """
    Check-in workflow:
    1. Transition status to checked_in
    2. Set room status to occupied
    3. Create GuestVerification records (Form A, Form C if foreign)
    4. Record actual check-in time
    """
    transition_reservation(reservation, "checked_in")
    reservation.actual_check_in_time = timezone.now()
    reservation.save(update_fields=["actual_check_in_time"])

    # Update room status
    for res_room in reservation.rooms.select_related("room"):
        room = res_room.room
        room.status = "occupied"
        room.save(update_fields=["status"])

    # Create verification records
    guest = reservation.guest
    hotel = reservation.hotel

    GuestVerification.objects.create(
        guest=guest, reservation=reservation, hotel=hotel,
        form_type="form_a", status="pending",
    )

    if guest.is_foreign:
        GuestVerification.objects.create(
            guest=guest, reservation=reservation, hotel=hotel,
            form_type="form_c", status="pending",
        )

    return reservation


@transaction.atomic
def perform_check_out(reservation, staff_user):
    """
    Check-out workflow:
    1. Transition status to checked_out
    2. Set room status to dirty
    3. Create housekeeping task
    4. Settle folio if balance = 0
    5. Record actual check-out time
    """
    transition_reservation(reservation, "checked_out")
    reservation.actual_check_out_time = timezone.now()
    reservation.save(update_fields=["actual_check_out_time"])

    # Update room status and create housekeeping tasks
    for res_room in reservation.rooms.select_related("room"):
        room = res_room.room
        room.status = "dirty"
        room.save(update_fields=["status"])

        HousekeepingTask.objects.create(
            hotel=reservation.hotel,
            room=room,
            task_type="cleaning",
            status="pending",
        )

    # Settle folio
    try:
        folio = reservation.folio
        folio.recalculate()
        if folio.balance <= 0:
            folio.status = "settled"
            folio.closed_at = timezone.now()
            folio.save(update_fields=["status", "closed_at"])
    except Exception:
        pass

    return reservation


@transaction.atomic
def perform_cancellation(reservation, staff_user):
    """
    Cancellation workflow:
    1. Calculate cancellation fee based on rate plan policy
    2. Post cancellation charge if applicable
    3. Transition to cancelled
    4. Release room
    """
    # Calculate cancellation fee
    fee = _calculate_cancellation_fee(reservation)

    if fee > 0:
        try:
            folio = reservation.folio
        except Exception:
            folio = create_folio(reservation)

        FolioCharge.objects.create(
            folio=folio,
            charge_type="cancellation_fee",
            description="Late cancellation fee",
            amount=fee,
            charge_date=date.today(),
            created_by=staff_user,
        )
        folio.recalculate()

    transition_reservation(reservation, "cancelled")

    # Release rooms
    for res_room in reservation.rooms.select_related("room"):
        room = res_room.room
        if room.status == "occupied":
            room.status = "available"
            room.save(update_fields=["status"])

    # Void folio if no charges
    try:
        folio = reservation.folio
        if folio.total_charges <= 0:
            folio.status = "void"
            folio.save(update_fields=["status"])
    except Exception:
        pass

    return reservation


@transaction.atomic
def perform_walk_in(hotel, guest, room, room_type, nights, staff_user, source="walk_in"):
    """
    Walk-in: create reservation + immediate check-in in one step.
    """
    from datetime import timedelta

    check_in_date = date.today()
    check_out_date = check_in_date + timedelta(days=nights)

    reservation = create_reservation(
        hotel=hotel,
        guest=guest,
        room=room,
        room_type=room_type,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        source=source,
        created_by=staff_user,
    )

    perform_check_in(reservation, staff_user)
    return reservation


def _calculate_cancellation_fee(reservation):
    """Calculate cancellation fee based on rate plan policy."""
    res_room = reservation.rooms.first()
    if not res_room or not res_room.rate_plan:
        return Decimal("0")

    rate_plan = res_room.rate_plan
    policy = rate_plan.cancellation_policy

    if policy == "free":
        return Decimal("0")

    if policy == "non_refundable":
        # Full booking amount
        total = sum(nr.rate for nr in res_room.nightly_rates.all())
        return total

    # moderate or strict: check if within cancellation window
    from django.utils import timezone as tz

    hours_until = (
        timezone.datetime.combine(reservation.check_in_date, timezone.datetime.min.time())
        - timezone.now().replace(tzinfo=None)
    ).total_seconds() / 3600

    if hours_until > rate_plan.cancellation_hours:
        return Decimal("0")  # Free cancellation (within window)

    if policy == "moderate":
        # First night charge
        first_night = res_room.nightly_rates.order_by("date").first()
        return first_night.rate if first_night else Decimal("0")

    if policy == "strict":
        total = sum(nr.rate for nr in res_room.nightly_rates.all())
        return total * rate_plan.cancellation_charge_percent / Decimal("100")

    return Decimal("0")
