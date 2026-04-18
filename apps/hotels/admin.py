from django.contrib import admin

from .models import Hotel, OTAConnection


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "city", "state", "phone", "is_active"]
    list_filter = ["is_active", "state"]
    search_fields = ["name", "code", "city"]


@admin.register(OTAConnection)
class OTAConnectionAdmin(admin.ModelAdmin):
    list_display = ["hotel", "channel", "connection_type", "sync_status", "is_active", "last_sync_at"]
    list_filter = ["channel", "sync_status", "is_active"]
    search_fields = ["hotel__name", "external_property_id"]
