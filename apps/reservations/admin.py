from django.contrib import admin

from .models import Reservation, ReservationRoom, RoomNightRate


class ReservationRoomInline(admin.TabularInline):
    model = ReservationRoom
    extra = 0


class RoomNightRateInline(admin.TabularInline):
    model = RoomNightRate
    extra = 0


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        "confirmation_number", "hotel", "guest", "check_in_date",
        "check_out_date", "status", "source", "created_at",
    ]
    list_filter = ["hotel", "status", "source"]
    search_fields = ["confirmation_number", "guest__first_name", "guest__last_name", "guest__phone"]
    inlines = [ReservationRoomInline]
    date_hierarchy = "check_in_date"


@admin.register(ReservationRoom)
class ReservationRoomAdmin(admin.ModelAdmin):
    list_display = ["reservation", "room", "room_type", "check_in_date", "check_out_date"]
    inlines = [RoomNightRateInline]
