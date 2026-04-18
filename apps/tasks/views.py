import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.billing.night_audit import run_night_audit_all_hotels


@csrf_exempt
@require_POST
def night_audit_task(request):
    """Endpoint for Cloud Scheduler to trigger nightly audit."""
    results = run_night_audit_all_hotels()
    return JsonResponse({"status": "ok", "results": results})
