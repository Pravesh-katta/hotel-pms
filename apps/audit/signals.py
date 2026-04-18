import logging
import threading

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.billing.models import Folio, FolioCharge
from apps.payments.models import Payment
from apps.reservations.models import Reservation
from apps.rooms.models import Room

from .models import AuditLog

logger = logging.getLogger(__name__)

_thread_local = threading.local()


def get_current_user():
    return getattr(_thread_local, "user", None)


def get_current_ip():
    return getattr(_thread_local, "ip", None)


def set_audit_context(user, ip=None):
    _thread_local.user = user
    _thread_local.ip = ip


def _create_log(instance, action, changes=None):
    try:
        hotel = getattr(instance, "hotel", None)
        AuditLog.objects.create(
            hotel=hotel,
            user=get_current_user(),
            action=action,
            model_name=instance.__class__.__name__,
            object_id=str(instance.pk),
            changes=changes or {},
            ip_address=get_current_ip(),
        )
    except Exception as e:
        logger.error(f"Audit log failed: {e}")


@receiver(post_save, sender=Reservation)
def log_reservation(sender, instance, created, **kwargs):
    action = "reservation.created" if created else f"reservation.{instance.status}"
    _create_log(instance, action, {
        "status": instance.status,
        "guest": str(instance.guest),
        "confirmation_number": instance.confirmation_number,
    })


@receiver(post_save, sender=Room)
def log_room_status(sender, instance, created, **kwargs):
    if not created:
        _create_log(instance, "room.status_changed", {"status": instance.status})


@receiver(post_save, sender=Payment)
def log_payment(sender, instance, created, **kwargs):
    if created:
        _create_log(instance, "payment.created", {
            "amount": str(instance.amount),
            "method": instance.method,
            "status": instance.status,
        })
