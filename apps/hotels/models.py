import uuid

from django.conf import settings
from django.db import models


class HotelGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, unique=True, help_text="URL-safe identifier, e.g. 'jasper-hotels'")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Hotel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(
        HotelGroup, on_delete=models.PROTECT, null=True, blank=True,
        related_name="hotels",
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True, help_text="Short code, e.g. MUM01")
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default="India")
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    currency = models.CharField(max_length=3, default="INR")
    timezone = models.CharField(max_length=50, default="Asia/Kolkata")
    max_rooms = models.PositiveIntegerField(default=15)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class OTAConnection(models.Model):
    CHANNEL_CHOICES = [
        ("airbnb", "Airbnb"),
        ("booking_com", "Booking.com"),
        ("goibibo", "Goibibo"),
        ("makemytrip", "MakeMyTrip"),
        ("agoda", "Agoda"),
        ("expedia", "Expedia"),
        ("other", "Other"),
    ]
    CONNECTION_TYPE_CHOICES = [
        ("direct_api", "Direct API"),
        ("channel_manager", "Channel Manager"),
        ("ical", "iCal Sync"),
    ]
    SYNC_STATUS_CHOICES = [
        ("ok", "OK"),
        ("error", "Error"),
        ("never_synced", "Never Synced"),
    ]

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="ota_connections")
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    connection_type = models.CharField(max_length=20, choices=CONNECTION_TYPE_CHOICES)
    channel_manager_name = models.CharField(max_length=100, blank=True)
    external_property_id = models.CharField(max_length=100, blank=True)
    api_key_id = models.CharField(max_length=200, blank=True)
    ical_url = models.URLField(max_length=500, blank=True)
    webhook_url = models.URLField(max_length=500, blank=True)
    sync_bookings = models.BooleanField(default=True)
    sync_rates = models.BooleanField(default=False)
    sync_availability = models.BooleanField(default=True)
    rate_plan = models.ForeignKey(
        "rates.RatePlan", on_delete=models.SET_NULL, null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_error = models.TextField(blank=True)
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES, default="never_synced")
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["hotel", "channel"]

    def __str__(self):
        return f"{self.hotel.code} — {self.get_channel_display()}"
