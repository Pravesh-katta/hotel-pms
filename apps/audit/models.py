from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    hotel = models.ForeignKey(
        "hotels.Hotel", on_delete=models.CASCADE, null=True, blank=True, related_name="audit_logs"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    action = models.CharField(max_length=50, help_text="e.g. reservation.created, room.status_changed")
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=50)
    changes = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["hotel", "created_at"]),
        ]

    def __str__(self):
        return f"{self.action} by {self.user} at {self.created_at}"


class DailyAuditSnapshot(models.Model):
    AUDIT_STATUS_CHOICES = [
        ("completed", "Completed"),
        ("partial", "Partial"),
        ("failed", "Failed"),
    ]

    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.CASCADE, related_name="audit_snapshots")
    audit_date = models.DateField()
    total_rooms = models.PositiveIntegerField(default=0)
    occupied_rooms = models.PositiveIntegerField(default=0)
    occupancy_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    revenue_posted = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_outstanding = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    noshow_count = models.PositiveIntegerField(default=0)
    arrivals_tomorrow = models.PositiveIntegerField(default=0)
    departures_tomorrow = models.PositiveIntegerField(default=0)
    audit_status = models.CharField(max_length=20, choices=AUDIT_STATUS_CHOICES, default="completed")
    error_message = models.TextField(blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ["hotel", "audit_date"]
        ordering = ["-audit_date"]

    def __str__(self):
        return f"{self.hotel.code} — {self.audit_date} ({self.get_audit_status_display()})"
