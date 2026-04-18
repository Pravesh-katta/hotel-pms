from django.db.models import Q

from apps.reservations.models import ReservationRoom

from .models import Room


def get_available_rooms(hotel, check_in, check_out, room_type=None):
    """
    Returns rooms that are available (not booked) for the given date range.
    A room is unavailable if any active ReservationRoom overlaps with the dates.
    """
    # Get all rooms for the hotel
    rooms = Room.objects.filter(
        hotel=hotel,
        is_active=True,
        status__in=["available", "dirty"],  # dirty rooms can still be booked for future dates
    )
    if room_type:
        rooms = rooms.filter(room_type=room_type)

    # Find rooms with overlapping reservations
    booked_room_ids = ReservationRoom.objects.filter(
        room__hotel=hotel,
        reservation__status__in=["confirmed", "checked_in"],
        check_in_date__lt=check_out,
        check_out_date__gt=check_in,
    ).values_list("room_id", flat=True)

    return rooms.exclude(id__in=booked_room_ids).select_related("room_type")


def is_room_available(room, check_in, check_out):
    """Check if a specific room is available for the given dates."""
    conflicts = ReservationRoom.objects.filter(
        room=room,
        reservation__status__in=["confirmed", "checked_in"],
        check_in_date__lt=check_out,
        check_out_date__gt=check_in,
    ).exists()
    return not conflicts
