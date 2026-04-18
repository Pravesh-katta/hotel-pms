from django.db import models


class Notification(models.Model):
    RECIPIENT_TYPE_CHOICES = [
        ("guest", "Guest"),
        ("staff", "Staff"),
        ("admin", "Admin"),
    ]
    CHANNEL_CHOICES = [
        ("whatsapp", "WhatsApp"),
        ("sms", "SMS"),
        ("email", "Email"),
        ("in_app", "In-App"),
    ]
    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("sent", "Sent"),
        ("delivered", "Delivered"),
        ("failed", "Failed"),
        ("read", "Read"),
    ]

    hotel = models.ForeignKey(
        "hotels.Hotel", on_delete=models.CASCADE, null=True, blank=True, related_name="notifications"
    )
    recipient_type = models.CharField(max_length=10, choices=RECIPIENT_TYPE_CHOICES)
    recipient_phone = models.CharField(max_length=15, blank=True)
    recipient_email = models.EmailField(blank=True)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    template_name = models.CharField(max_length=100)
    context_data = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="queued")
    external_id = models.CharField(max_length=100, blank=True, help_text="MSG91 message ID")
    error_message = models.TextField(blank=True)
    related_model = models.CharField(max_length=50, blank=True)
    related_id = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["hotel", "status"]),
        ]

    def __str__(self):
        return f"{self.template_name} → {self.recipient_phone or self.recipient_email} ({self.get_status_display()})"


class NotificationPreference(models.Model):
    hotel = models.OneToOneField(
        "hotels.Hotel", on_delete=models.CASCADE, related_name="notification_prefs"
    )
    whatsapp_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    send_booking_confirm = models.BooleanField(default=True)
    send_checkin_reminder = models.BooleanField(default=True)
    send_payment_receipt = models.BooleanField(default=True)
    send_checkout_summary = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification Prefs — {self.hotel.code}"
