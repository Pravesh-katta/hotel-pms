from django.conf import settings
from django.db import models


class Payment(models.Model):
    METHOD_CHOICES = [
        ("upi", "UPI"),
        ("credit_card", "Credit Card"),
        ("debit_card", "Debit Card"),
        ("net_banking", "Net Banking"),
        ("wallet", "Wallet"),
        ("cash", "Cash"),
        ("bank_transfer", "Bank Transfer"),
        ("corporate", "Corporate"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.CASCADE, related_name="payments")
    folio = models.ForeignKey("billing.Folio", on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount in INR")
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    razorpay_order_id = models.CharField(max_length=50, blank=True)
    razorpay_payment_id = models.CharField(max_length=50, blank=True)
    razorpay_signature = models.CharField(max_length=200, blank=True)
    reference_number = models.CharField(max_length=100, blank=True, help_text="For manual payments")
    original_payment = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="refunds", help_text="Links refund to original payment"
    )
    refund_reason = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["hotel", "status"]),
        ]

    def __str__(self):
        return f"₹{self.amount} via {self.get_method_display()} ({self.get_status_display()})"


class HotelPaymentConfig(models.Model):
    hotel = models.OneToOneField(
        "hotels.Hotel", on_delete=models.CASCADE, related_name="payment_config"
    )
    razorpay_key_id = models.CharField(max_length=50, blank=True, help_text="Public key (safe in DB)")
    razorpay_account_id = models.CharField(max_length=50, blank=True, help_text="For Razorpay Route")
    gst_number = models.CharField(max_length=20, blank=True, help_text="Hotel GSTIN")
    gst_rate = models.DecimalField(max_digits=4, decimal_places=2, default=12.00)
    sac_code = models.CharField(max_length=10, default="9963")
    accepts_online_payment = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment Config — {self.hotel.code}"
