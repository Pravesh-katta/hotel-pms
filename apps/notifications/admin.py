from django.contrib import admin

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["template_name", "channel", "recipient_phone", "status", "hotel", "created_at"]
    list_filter = ["hotel", "channel", "status", "template_name"]
    search_fields = ["recipient_phone", "recipient_email"]


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ["hotel", "whatsapp_enabled", "sms_enabled", "email_enabled"]
