from django.contrib import admin

from .models import Folio, FolioCharge


class FolioChargeInline(admin.TabularInline):
    model = FolioCharge
    extra = 0
    readonly_fields = ["created_at"]


@admin.register(Folio)
class FolioAdmin(admin.ModelAdmin):
    list_display = ["folio_number", "hotel", "reservation", "total_charges", "total_payments", "balance", "status"]
    list_filter = ["hotel", "status"]
    search_fields = ["folio_number", "reservation__confirmation_number"]
    inlines = [FolioChargeInline]


@admin.register(FolioCharge)
class FolioChargeAdmin(admin.ModelAdmin):
    list_display = ["folio", "charge_type", "description", "amount", "charge_date"]
    list_filter = ["charge_type", "charge_date"]
