from django.contrib import admin

from .models import Guest, GuestVerification


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ["full_name", "hotel", "phone", "email", "nationality", "is_foreign", "created_at"]
    list_filter = ["hotel", "is_foreign", "nationality"]
    search_fields = ["first_name", "last_name", "phone", "email", "id_number"]


@admin.register(GuestVerification)
class GuestVerificationAdmin(admin.ModelAdmin):
    list_display = ["guest", "hotel", "form_type", "status", "submission_date", "created_at"]
    list_filter = ["hotel", "form_type", "status"]
    search_fields = ["guest__first_name", "guest__last_name", "reference_number"]
