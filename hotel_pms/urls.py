from django.contrib import admin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import include, path


def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("", lambda r: redirect("dashboard_home")),
    path("health/", health_check, name="health_check"),
    path("superadmin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),
    path("dashboard/", include("apps.hotels.urls")),
    path("dashboard/rooms/", include("apps.rooms.urls")),
    path("dashboard/calendar/", include("apps.rooms.urls_calendar")),
    path("dashboard/guests/", include("apps.guests.urls")),
    path("dashboard/reservations/", include("apps.reservations.urls")),
    path("dashboard/billing/", include("apps.billing.urls")),
    path("dashboard/payments/", include("apps.payments.urls")),
    path("dashboard/housekeeping/", include("apps.housekeeping.urls")),
    path("dashboard/rates/", include("apps.rates.urls")),
    path("dashboard/reports/", include("apps.reports.urls")),
    path("dashboard/search/", include("apps.search.urls")),
    path("dashboard/staff/", include("apps.accounts.urls_staff")),
    path("dashboard/settings/", include("apps.notifications.urls")),
    path("dashboard/settings/ota/", include("apps.hotels.urls_ota")),
    path("api/tasks/", include("apps.tasks.urls")),
    path("api/webhooks/", include("apps.payments.urls_webhooks")),
]

admin.site.site_header = "Hotel PMS Administration"
admin.site.site_title = "Hotel PMS"
admin.site.index_title = "System Administration"
