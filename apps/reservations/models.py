from django.conf import settings
from django.db import models


class Reservation(models.Model):
    STATUS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("checked_in", "Checked In"),
        ("checked_out", "Checked Out"),
        ("cancelled", "Cancelled"),
        ("no_show", "No Show"),
    ]
    SOURCE_CHOICES = [
        ("walk_in", "Walk-in"),
        ("phone", "Phone"),
        ("website", "Website"),
        ("airbnb", "Airbnb"),
        ("booking_com", "Booking.com"),
        ("ota_other", "Other OTA"),
    ]

    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.CASCADE, related_name="reservations")
    confirmation_number = models.CharField(max_length=20)
    guest = models.ForeignKey("guests.Guest", on_delete=models.PROTECT, related_name="reservations")
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="confirmed")
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="walk_in")
    external_booking_id = models.CharField(max_length=100, blank=True)
    num_adults = models.PositiveIntegerField(default=1)
    num_children = models.PositiveIntegerField(default=0)
    special_requests = models.TextField(blank=True)
    actual_check_in_time = models.DateTimeField(null=True, blank=True)
    actual_check_out_time = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [
            ("hotel", "confirmation_number"),
        ]
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["hotel", "status"]),
            models.Index(fields=["hotel", "check_in_date"]),
        ]

    def __str__(self):
        return f"#{self.confirmation_number} — {self.guest} ({self.get_status_display()})"

    @property
    def num_nights(self):
        return (self.check_out_date - self.check_in_date).days


class ReservationRoom(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name="rooms")
    room = models.ForeignKey("rooms.Room", on_delete=models.PROTECT, related_name="reservation_rooms")
    room_type = models.ForeignKey("rooms.RoomType", on_delete=models.PROTECT)
    rate_plan = models.ForeignKey("rates.RatePlan", on_delete=models.SET_NULL, null=True, blank=True)
    check_in_date = models.DateField()
    check_out_date = models.DateField()

    class Meta:
        indexes = [
            models.Index(fields=["room", "check_in_date", "check_out_date"]),
        ]

    def __str__(self):
        return f"Room {self.room.room_number} for #{self.reservation.confirmation_number}"


class RoomNightRate(models.Model):
    reservation_room = models.ForeignKey(
        ReservationRoom, on_delete=models.CASCADE, related_name="nightly_rates"
    )
    date = models.DateField()
    rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Rate in INR for this night")

    class Meta:
        unique_together = ["reservation_room", "date"]
        ordering = ["date"]

    def __str__(self):
        return f"Room {self.reservation_room.room.room_number} — {self.date}: ₹{self.rate}"
