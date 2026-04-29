from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import HotelMembership, StaffProfile


@admin.register(HotelMembership)
class HotelMembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "hotel", "role", "is_active", "created_at"]
    list_filter = ["role", "is_active", "hotel"]
    search_fields = ["user__username", "user__email", "hotel__name", "hotel__code"]
    autocomplete_fields = ["user", "hotel"]
    list_select_related = ["user", "hotel"]


class StaffProfileInline(admin.StackedInline):
    model = StaffProfile
    can_delete = False
    verbose_name_plural = "Staff Profile"


class UserAdmin(BaseUserAdmin):
    inlines = [StaffProfileInline]
    list_display = ["username", "email", "first_name", "last_name", "get_hotel", "get_role", "is_active"]

    def get_hotel(self, obj):
        if hasattr(obj, "staffprofile"):
            return obj.staffprofile.hotel or "All Hotels"
        return "-"
    get_hotel.short_description = "Hotel"

    def get_role(self, obj):
        if hasattr(obj, "staffprofile"):
            return obj.staffprofile.get_role_display()
        return "-"
    get_role.short_description = "Role"


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
