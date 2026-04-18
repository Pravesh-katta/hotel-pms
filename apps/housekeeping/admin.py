from django.contrib import admin

from .models import HousekeepingTask


@admin.register(HousekeepingTask)
class HousekeepingTaskAdmin(admin.ModelAdmin):
    list_display = ["room", "hotel", "task_type", "status", "assigned_to", "created_at", "completed_at"]
    list_filter = ["hotel", "task_type", "status"]
    search_fields = ["room__room_number"]
