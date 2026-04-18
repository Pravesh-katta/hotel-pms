class InvalidTransition(Exception):
    pass


ALLOWED_TRANSITIONS = {
    "confirmed": ["checked_in", "cancelled", "no_show"],
    "checked_in": ["checked_out"],
    "checked_out": [],  # final state
    "cancelled": [],  # final state
    "no_show": [],  # final state
}


def validate_transition(current_status, new_status):
    allowed = ALLOWED_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise InvalidTransition(
            f"Cannot transition from '{current_status}' to '{new_status}'. "
            f"Allowed transitions: {allowed or 'none (final state)'}"
        )


def transition_reservation(reservation, new_status):
    validate_transition(reservation.status, new_status)
    reservation.status = new_status
    reservation.save(update_fields=["status", "updated_at"])
    return reservation
