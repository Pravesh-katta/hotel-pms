from django.db import models


class RatePlan(models.Model):
    PLAN_TYPE_CHOICES = [
        ("standard", "Standard"),
        ("ota", "OTA"),
        ("corporate", "Corporate"),
        ("promotional", "Promotional"),
        ("long_stay", "Long Stay"),
    ]
    SOURCE_CHOICES = [
        ("walk_in", "Walk-in"),
        ("phone", "Phone"),
        ("website", "Website"),
        ("airbnb", "Airbnb"),
        ("booking_com", "Booking.com"),
        ("ota_other", "Other OTA"),
    ]
    CANCELLATION_CHOICES = [
        ("free", "Free Cancellation"),
        ("moderate", "Moderate"),
        ("strict", "Strict"),
        ("non_refundable", "Non-Refundable"),
    ]

    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.CASCADE, related_name="rate_plans")
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPE_CHOICES, default="standard")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, null=True, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text="Higher priority wins if multiple plans match")
    min_stay_nights = models.PositiveIntegerField(default=1)
    advance_days = models.PositiveIntegerField(null=True, blank=True)
    cancellation_policy = models.CharField(max_length=20, choices=CANCELLATION_CHOICES, default="moderate")
    cancellation_hours = models.PositiveIntegerField(default=24)
    cancellation_charge_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["hotel", "-priority", "name"]

    def __str__(self):
        return f"{self.name} — {self.hotel.code}"


class RatePlanRate(models.Model):
    rate_plan = models.ForeignKey(RatePlan, on_delete=models.CASCADE, related_name="rates")
    room_type = models.ForeignKey("rooms.RoomType", on_delete=models.CASCADE, related_name="rate_plan_rates")
    base_rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="INR per night")
    extra_adult_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    extra_child_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["rate_plan", "room_type"]

    def __str__(self):
        return f"{self.rate_plan.name} / {self.room_type.name} — ₹{self.base_rate}"


class SeasonalRate(models.Model):
    rate_plan_rate = models.ForeignKey(RatePlanRate, on_delete=models.CASCADE, related_name="seasonal_rates")
    name = models.CharField(max_length=100, help_text="e.g. Diwali Peak, Monsoon Off-Peak")
    start_date = models.DateField()
    end_date = models.DateField()
    rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Overrides base_rate for these dates")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["start_date"]

    def __str__(self):
        return f"{self.name}: ₹{self.rate} ({self.start_date} — {self.end_date})"
