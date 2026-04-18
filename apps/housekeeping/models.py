from django.conf import settings
from django.db import models


class HousekeepingTask(models.Model):
    TASK_TYPE_CHOICES = [
        ("cleaning", "Cleaning"),
        ("inspection", "Inspection"),
        ("maintenance", "Maintenance"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    ]

    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.CASCADE, related_name="housekeeping_tasks")
    room = models.ForeignKey("rooms.Room", on_delete=models.CASCADE, related_name="housekeeping_tasks")
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default="cleaning")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Room {self.room.room_number} — {self.get_task_type_display()} ({self.get_status_display()})"
