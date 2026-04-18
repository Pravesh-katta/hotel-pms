from django.contrib import admin

from .models import HotelPaymentConfig, Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["hotel", "folio", "amount", "method", "status", "created_at"]
    list_filter = ["hotel", "method", "status"]
    search_fields = ["razorpay_payment_id", "razorpay_order_id", "reference_number"]


@admin.register(HotelPaymentConfig)
class HotelPaymentConfigAdmin(admin.ModelAdmin):
    list_display = ["hotel", "gst_number", "gst_rate", "accepts_online_payment"]
