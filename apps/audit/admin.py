from django.contrib import admin

from .models import AuditLog, DailyAuditSnapshot


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["action", "model_name", "object_id", "user", "hotel", "created_at"]
    list_filter = ["hotel", "action", "model_name"]
    search_fields = ["action", "object_id"]
    readonly_fields = ["hotel", "user", "action", "model_name", "object_id", "changes", "ip_address", "created_at"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DailyAuditSnapshot)
class DailyAuditSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        "hotel", "audit_date", "occupied_rooms", "total_rooms",
        "occupancy_percent", "revenue_posted", "audit_status",
    ]
    list_filter = ["hotel", "audit_status"]
    date_hierarchy = "audit_date"
