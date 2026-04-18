from django.urls import path

from .webhooks import razorpay_webhook

urlpatterns = [
    path("razorpay/", razorpay_webhook, name="razorpay_webhook"),
]
