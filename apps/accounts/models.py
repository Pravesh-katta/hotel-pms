from django.conf import settings
from django.db import models


class StaffProfile(models.Model):
    ROLE_CHOICES = [
        ("super_admin", "Super Admin"),
        ("hotel_admin", "Hotel Admin"),
        ("manager", "Manager"),
        ("front_desk", "Front Desk"),
        ("housekeeping", "Housekeeping"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="staffprofile"
    )
    hotel = models.ForeignKey(
        "hotels.Hotel", on_delete=models.CASCADE, null=True, blank=True,
        related_name="staff", help_text="Null for super_admin (sees all hotels)"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self):
        hotel_name = self.hotel.code if self.hotel else "ALL"
        return f"{self.user.get_full_name() or self.user.username} ({hotel_name} / {self.get_role_display()})"

    @property
    def is_super_admin(self):
        return self.role == "super_admin"

    def has_role(self, *roles):
        return self.role in roles


class HotelMembership(models.Model):
    ROLE_CHOICES = [
        ("hotel_admin", "Hotel Admin"),
        ("manager", "Manager"),
        ("front_desk", "Front Desk"),
        ("housekeeping", "Housekeeping"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hotel_memberships"
    )
    hotel = models.ForeignKey(
        "hotels.Hotel", on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "hotel")]
        ordering = ["hotel__name", "user__username"]

    def __str__(self):
        return f"{self.user.username} @ {self.hotel.code} ({self.get_role_display()})"
