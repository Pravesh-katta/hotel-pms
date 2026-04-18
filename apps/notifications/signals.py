import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.payments.models import Payment
from apps.reservations.models import Reservation

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Reservation)
def on_reservation_change(sender, instance, created, **kwargs):
    """Send notifications on reservation status changes."""
    from .services import send_notification

    guest = instance.guest
    hotel = instance.hotel

    if created and instance.status == "confirmed":
        send_notification(
            hotel=hotel,
            template_name="booking_confirmation",
            recipient_phone=guest.phone,
            recipient_email=guest.email,
            context_data={
                "subject": f"Booking Confirmed — {hotel.name} | {instance.confirmation_number}",
                "guest_name": guest.full_name,
                "hotel_name": hotel.name,
                "hotel_address": hotel.address,
                "hotel_phone": hotel.phone,
                "confirmation_number": instance.confirmation_number,
                "check_in_date": str(instance.check_in_date),
                "check_out_date": str(instance.check_out_date),
            },
            related_model="Reservation",
            related_id=instance.pk,
        )

    elif instance.status == "cancelled":
        send_notification(
            hotel=hotel,
            template_name="cancellation",
            recipient_phone=guest.phone,
            recipient_email=guest.email,
            context_data={
                "subject": f"Booking Cancelled — {hotel.name} | {instance.confirmation_number}",
                "guest_name": guest.full_name,
                "hotel_name": hotel.name,
                "confirmation_number": instance.confirmation_number,
            },
            related_model="Reservation",
            related_id=instance.pk,
        )


@receiver(post_save, sender=Payment)
def on_payment_completed(sender, instance, **kwargs):
    """Send payment receipt when payment is completed."""
    if instance.status != "completed":
        return

    from .services import send_notification

    folio = instance.folio
    guest = folio.reservation.guest
    hotel = instance.hotel

    send_notification(
        hotel=hotel,
        template_name="payment_receipt",
        recipient_phone=guest.phone,
        recipient_email=guest.email,
        context_data={
            "subject": f"Payment Received — ₹{instance.amount} | {hotel.name}",
            "guest_name": guest.full_name,
            "hotel_name": hotel.name,
            "amount": str(instance.amount),
            "method": instance.get_method_display(),
            "confirmation_number": folio.reservation.confirmation_number,
            "balance": str(folio.balance),
        },
        related_model="Payment",
        related_id=instance.pk,
    )
