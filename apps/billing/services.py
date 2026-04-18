from datetime import date
from decimal import Decimal

from django.utils import timezone

from .models import Folio, FolioCharge


def create_folio(reservation):
    """Create a folio for a reservation with auto-generated folio number."""
    hotel = reservation.hotel
    last_folio = Folio.objects.filter(hotel=hotel).order_by("-created_at").first()
    if last_folio and last_folio.folio_number:
        try:
            num = int(last_folio.folio_number.split("-")[1]) + 1
        except (IndexError, ValueError):
            num = 1
    else:
        num = 1

    folio_number = f"INV-{num:04d}"

    folio = Folio.objects.create(
        hotel=hotel,
        reservation=reservation,
        folio_number=folio_number,
        status="open",
    )
    return folio


def post_room_charges(folio, reservation_room, charge_date, created_by=None):
    """
    Post room charge + GST for a single night.
    Idempotent — skips if charge already exists for this date.
    """
    existing = FolioCharge.objects.filter(
        folio=folio,
        charge_type="room_charge",
        charge_date=charge_date,
    ).exists()
    if existing:
        return  # already posted

    # Get rate for this night
    from apps.reservations.models import RoomNightRate

    try:
        night_rate = RoomNightRate.objects.get(
            reservation_room=reservation_room, date=charge_date
        )
        rate = night_rate.rate
    except RoomNightRate.DoesNotExist:
        rate = reservation_room.room_type.base_rate

    # Post room charge
    FolioCharge.objects.create(
        folio=folio,
        charge_type="room_charge",
        description=f"Room {reservation_room.room.room_number} — {charge_date}",
        amount=rate,
        charge_date=charge_date,
        created_by=created_by,
    )

    # Calculate and post GST
    gst_rate = get_gst_rate(rate)
    half_gst = (rate * gst_rate / Decimal("100")) / 2

    FolioCharge.objects.create(
        folio=folio,
        charge_type="cgst",
        description=f"CGST {gst_rate / 2}%",
        amount=half_gst.quantize(Decimal("0.01")),
        charge_date=charge_date,
        created_by=created_by,
    )
    FolioCharge.objects.create(
        folio=folio,
        charge_type="sgst",
        description=f"SGST {gst_rate / 2}%",
        amount=half_gst.quantize(Decimal("0.01")),
        charge_date=charge_date,
        created_by=created_by,
    )

    folio.recalculate()


def get_gst_rate(room_rate):
    """Returns GST rate based on room tariff slab."""
    if room_rate > Decimal("7500"):
        return Decimal("18")
    return Decimal("12")


def post_all_room_charges(folio, created_by=None):
    """Post room charges for all nights of the reservation."""
    reservation = folio.reservation
    for res_room in reservation.rooms.all():
        for night_rate in res_room.nightly_rates.all():
            post_room_charges(folio, res_room, night_rate.date, created_by)
