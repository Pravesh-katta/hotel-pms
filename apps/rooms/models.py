from django.db import models


class RoomType(models.Model):
    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.CASCADE, related_name="room_types")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    base_rate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Default nightly rate in INR")
    max_occupancy = models.PositiveIntegerField(default=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["hotel", "name"]
        ordering = ["hotel", "name"]

    def __str__(self):
        return f"{self.name} — {self.hotel.code}"


class Room(models.Model):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("occupied", "Occupied"),
        ("dirty", "Dirty"),
        ("maintenance", "Maintenance"),
        ("blocked", "Blocked"),
    ]

    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.CASCADE, related_name="rooms")
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, related_name="rooms")
    room_number = models.CharField(max_length=10)
    floor = models.CharField(max_length=10, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["hotel", "room_number"]
        ordering = ["hotel", "room_number"]

    def __str__(self):
        return f"Room {self.room_number} ({self.room_type.name}) — {self.hotel.code}"
