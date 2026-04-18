from django.urls import path

from .views import night_audit_task

urlpatterns = [
    path("night-audit/", night_audit_task, name="night_audit_task"),
]
