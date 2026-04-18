import logging

from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Notification, NotificationPreference

logger = logging.getLogger(__name__)


def send_notification(hotel, template_name, recipient_phone="", recipient_email="",
                      context_data=None, related_model="", related_id=""):
    """
    Create and dispatch a notification.
    Checks hotel's notification preferences before sending.
    """
    if context_data is None:
        context_data = {}

    # Check preferences
    try:
        prefs = hotel.notification_prefs
    except NotificationPreference.DoesNotExist:
        prefs = None

    # Determine channel
    channel = "email"
    if recipient_phone and prefs and prefs.whatsapp_enabled:
        channel = "whatsapp"
    elif recipient_phone and prefs and prefs.sms_enabled:
        channel = "sms"

    # Create notification record
    notification = Notification.objects.create(
        hotel=hotel,
        recipient_type="guest",
        recipient_phone=recipient_phone,
        recipient_email=recipient_email,
        channel=channel,
        template_name=template_name,
        context_data=context_data,
        status="queued",
        related_model=related_model,
        related_id=str(related_id),
    )

    # Dispatch
    try:
        if channel == "email" and recipient_email:
            _send_email(notification, context_data)
        elif channel in ("whatsapp", "sms"):
            # MSG91 integration — placeholder for now
            logger.info(f"Would send {channel} to {recipient_phone}: {template_name}")
            notification.status = "sent"
            notification.save(update_fields=["status"])
        else:
            notification.status = "sent"
            notification.save(update_fields=["status"])
    except Exception as e:
        notification.status = "failed"
        notification.error_message = str(e)
        notification.save(update_fields=["status", "error_message"])
        logger.error(f"Notification failed: {e}")

    return notification


def _send_email(notification, context_data):
    """Send email notification using Django's email backend."""
    template_map = {
        "booking_confirmation": "emails/booking_confirmation.html",
        "payment_receipt": "emails/payment_receipt.html",
        "checkout_summary": "emails/checkout_summary.html",
        "cancellation": "emails/cancellation.html",
    }

    template = template_map.get(notification.template_name)
    if not template:
        notification.status = "sent"
        notification.save(update_fields=["status"])
        return

    try:
        html_content = render_to_string(template, context_data)
        subject = context_data.get("subject", f"Hotel PMS — {notification.template_name}")

        send_mail(
            subject=subject,
            message="",
            html_message=html_content,
            from_email=None,
            recipient_list=[notification.recipient_email],
            fail_silently=False,
        )
        notification.status = "sent"
        from django.utils import timezone
        notification.sent_at = timezone.now()
        notification.save(update_fields=["status", "sent_at"])
    except Exception as e:
        raise
