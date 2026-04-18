from django.contrib import admin

from .models import Room, RoomType


class RoomInline(admin.TabularInline):
    model = Room
    extra = 0


@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "hotel", "base_rate", "max_occupancy"]
    list_filter = ["hotel"]
    search_fields = ["name"]
    inlines = [RoomInline]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["room_number", "hotel", "room_type", "floor", "status", "is_active"]
    list_filter = ["hotel", "status", "room_type", "is_active"]
    search_fields = ["room_number"]
