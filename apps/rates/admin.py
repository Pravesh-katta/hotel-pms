from django.contrib import admin

from .models import RatePlan, RatePlanRate, SeasonalRate


class RatePlanRateInline(admin.TabularInline):
    model = RatePlanRate
    extra = 0


class SeasonalRateInline(admin.TabularInline):
    model = SeasonalRate
    extra = 0


@admin.register(RatePlan)
class RatePlanAdmin(admin.ModelAdmin):
    list_display = ["name", "hotel", "plan_type", "source", "is_default", "is_active", "priority"]
    list_filter = ["hotel", "plan_type", "is_active", "is_default"]
    search_fields = ["name"]
    inlines = [RatePlanRateInline]


@admin.register(RatePlanRate)
class RatePlanRateAdmin(admin.ModelAdmin):
    list_display = ["rate_plan", "room_type", "base_rate", "extra_adult_rate"]
    list_filter = ["rate_plan__hotel"]
    inlines = [SeasonalRateInline]
