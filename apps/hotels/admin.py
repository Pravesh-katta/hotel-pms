from django.contrib import admin

from .models import Hotel, HotelGroup, OTAConnection


@admin.register(HotelGroup)
class HotelGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "hotel_count", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}

    def hotel_count(self, obj):
        return obj.hotels.count()
    hotel_count.short_description = "Hotels"


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "group", "city", "state", "phone", "is_active"]
    list_filter = ["is_active", "state", "group"]
    search_fields = ["name", "code", "city"]
    list_select_related = ["group"]


@admin.register(OTAConnection)
class OTAConnectionAdmin(admin.ModelAdmin):
    list_display = ["hotel", "channel", "connection_type", "sync_status", "is_active", "last_sync_at"]
    list_filter = ["channel", "sync_status", "is_active"]
    search_fields = ["hotel__name", "external_property_id"]
