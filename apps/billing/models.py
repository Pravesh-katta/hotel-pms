from django.conf import settings
from django.db import models


class Folio(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("settled", "Settled"),
        ("void", "Void"),
    ]

    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.CASCADE, related_name="folios")
    reservation = models.OneToOneField(
        "reservations.Reservation", on_delete=models.CASCADE, related_name="folio"
    )
    folio_number = models.CharField(max_length=20)
    total_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_payments = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["hotel", "status"]),
        ]

    def __str__(self):
        return f"Folio {self.folio_number} — ₹{self.balance} ({self.get_status_display()})"

    def recalculate(self):
        self.total_charges = sum(
            c.amount for c in self.charges.all() if c.amount > 0
        )
        discount = abs(sum(
            c.amount for c in self.charges.all() if c.amount < 0
        ))
        self.total_charges -= discount
        self.total_payments = sum(
            p.amount for p in self.payments.filter(status="completed")
        )
        self.balance = self.total_charges - self.total_payments
        self.save(update_fields=["total_charges", "total_payments", "balance"])


class FolioCharge(models.Model):
    CHARGE_TYPE_CHOICES = [
        ("room_charge", "Room Charge"),
        ("cgst", "CGST"),
        ("sgst", "SGST"),
        ("igst", "IGST"),
        ("food_beverage", "Food & Beverage"),
        ("laundry", "Laundry"),
        ("minibar", "Minibar"),
        ("misc", "Miscellaneous"),
        ("discount", "Discount"),
        ("cancellation_fee", "Cancellation Fee"),
        ("no_show_fee", "No Show Fee"),
    ]

    folio = models.ForeignKey(Folio, on_delete=models.CASCADE, related_name="charges")
    charge_type = models.CharField(max_length=20, choices=CHARGE_TYPE_CHOICES)
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Positive=charge, Negative=discount")
    charge_date = models.DateField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["charge_date", "created_at"]
        indexes = [
            models.Index(fields=["folio", "charge_date"]),
        ]

    def __str__(self):
        return f"{self.get_charge_type_display()}: ₹{self.amount} ({self.charge_date})"
