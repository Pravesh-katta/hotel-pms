from django.urls import path
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import NotificationPreference


@login_required
def notification_settings(request):
    hotel = request.hotel
    if not hotel:
        return render(request, "dashboard/settings/notifications.html", {"prefs": None})

    prefs, _ = NotificationPreference.objects.get_or_create(hotel=hotel)

    if request.method == "POST":
        prefs.whatsapp_enabled = "whatsapp_enabled" in request.POST
        prefs.sms_enabled = "sms_enabled" in request.POST
        prefs.email_enabled = "email_enabled" in request.POST
        prefs.send_booking_confirm = "send_booking_confirm" in request.POST
        prefs.send_checkin_reminder = "send_checkin_reminder" in request.POST
        prefs.send_payment_receipt = "send_payment_receipt" in request.POST
        prefs.send_checkout_summary = "send_checkout_summary" in request.POST
        prefs.save()
        messages.success(request, "Notification settings updated.")
        return redirect("notification_settings")

    return render(request, "dashboard/settings/notifications.html", {"prefs": prefs})


urlpatterns = [
    path("notifications/", notification_settings, name="notification_settings"),
]
