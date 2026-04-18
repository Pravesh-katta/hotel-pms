import hashlib
import hmac
import json
import os

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Payment


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """
    Handle Razorpay webhook events.
    Verifies signature, then processes payment.captured and refund.processed events.
    """
    webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
    if not webhook_secret:
        return HttpResponseBadRequest("Webhook secret not configured")

    # Verify signature
    signature = request.headers.get("X-Razorpay-Signature", "")
    body = request.body

    expected = hmac.new(
        webhook_secret.encode(), body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        return HttpResponseBadRequest("Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    event = payload.get("event", "")

    if event == "payment.captured":
        _handle_payment_captured(payload)
    elif event == "refund.processed":
        _handle_refund_processed(payload)

    return HttpResponse("OK", status=200)


def _handle_payment_captured(payload):
    """Process a captured payment event."""
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payment_entity.get("order_id", "")
    payment_id = payment_entity.get("id", "")

    if not order_id:
        return

    try:
        payment = Payment.objects.get(razorpay_order_id=order_id)
        if payment.status == "pending":
            payment.razorpay_payment_id = payment_id
            payment.status = "completed"

            method_map = {
                "upi": "upi",
                "card": "credit_card",
                "netbanking": "net_banking",
                "wallet": "wallet",
            }
            payment.method = method_map.get(payment_entity.get("method", ""), "upi")
            payment.save()
            payment.folio.recalculate()
    except Payment.DoesNotExist:
        pass


def _handle_refund_processed(payload):
    """Process a refund event."""
    refund_entity = payload.get("payload", {}).get("refund", {}).get("entity", {})
    payment_id = refund_entity.get("payment_id", "")

    if not payment_id:
        return

    try:
        payment = Payment.objects.get(razorpay_payment_id=payment_id)
        if payment.status == "completed":
            payment.status = "refunded"
            payment.save(update_fields=["status"])
            payment.folio.recalculate()
    except Payment.DoesNotExist:
        pass
