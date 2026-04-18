import os
from decimal import Decimal

from django.db import transaction

from apps.billing.models import Folio

from .models import HotelPaymentConfig, Payment


def get_razorpay_client():
    """Get Razorpay client instance."""
    import razorpay

    key_id = os.environ.get("RAZORPAY_KEY_ID", "")
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
    if not key_id or not key_secret:
        return None
    return razorpay.Client(auth=(key_id, key_secret))


@transaction.atomic
def create_razorpay_order(folio, amount):
    """
    Create a Razorpay order and a pending Payment record.
    Amount in INR (rupees) — converted to paise for Razorpay.
    """
    client = get_razorpay_client()
    if not client:
        raise ValueError("Razorpay is not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.")

    amount_paise = int(amount * 100)

    order_data = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": folio.folio_number,
        "notes": {
            "hotel": str(folio.hotel.name),
            "folio": folio.folio_number,
            "guest": str(folio.reservation.guest),
        },
    }
    razorpay_order = client.order.create(data=order_data)

    payment = Payment.objects.create(
        hotel=folio.hotel,
        folio=folio,
        amount=amount,
        method="upi",  # Will be updated by webhook with actual method
        status="pending",
        razorpay_order_id=razorpay_order["id"],
    )

    return payment, razorpay_order


@transaction.atomic
def verify_razorpay_payment(razorpay_order_id, razorpay_payment_id, razorpay_signature):
    """
    Verify Razorpay payment signature and complete the payment.
    Returns the updated Payment object.
    """
    client = get_razorpay_client()
    if not client:
        raise ValueError("Razorpay not configured.")

    # Verify signature
    params = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
    }
    client.utility.verify_payment_signature(params)

    # Update payment
    payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
    payment.razorpay_payment_id = razorpay_payment_id
    payment.razorpay_signature = razorpay_signature
    payment.status = "completed"

    # Get actual payment method from Razorpay
    try:
        rz_payment = client.payment.fetch(razorpay_payment_id)
        method_map = {
            "upi": "upi",
            "card": "credit_card",
            "netbanking": "net_banking",
            "wallet": "wallet",
        }
        payment.method = method_map.get(rz_payment.get("method", ""), "upi")
    except Exception:
        pass

    payment.save()

    # Recalculate folio
    payment.folio.recalculate()

    return payment


@transaction.atomic
def record_cash_payment(folio, amount, received_by, reference_number="", notes=""):
    """Record a cash or bank transfer payment."""
    payment = Payment.objects.create(
        hotel=folio.hotel,
        folio=folio,
        amount=amount,
        method="cash",
        status="completed",
        reference_number=reference_number,
        notes=notes,
        received_by=received_by,
    )
    folio.recalculate()
    return payment


@transaction.atomic
def record_bank_transfer(folio, amount, reference_number, received_by, notes=""):
    """Record a bank transfer (NEFT/RTGS/IMPS) payment."""
    payment = Payment.objects.create(
        hotel=folio.hotel,
        folio=folio,
        amount=amount,
        method="bank_transfer",
        status="completed",
        reference_number=reference_number,
        notes=notes,
        received_by=received_by,
    )
    folio.recalculate()
    return payment


@transaction.atomic
def process_refund(payment, amount=None, reason=""):
    """
    Process a refund for a completed payment.
    For online payments, calls Razorpay refund API.
    For cash, creates a refund record immediately.
    """
    if payment.status != "completed":
        raise ValueError("Can only refund completed payments.")

    refund_amount = amount or payment.amount

    if refund_amount > payment.amount:
        raise ValueError("Refund amount cannot exceed payment amount.")

    # Online payment — call Razorpay
    if payment.razorpay_payment_id:
        client = get_razorpay_client()
        if client:
            refund_data = {
                "amount": int(refund_amount * 100),
            }
            client.payment.refund(payment.razorpay_payment_id, refund_data)

    # Create refund payment record
    refund = Payment.objects.create(
        hotel=payment.hotel,
        folio=payment.folio,
        amount=-refund_amount,  # Negative for refund
        method=payment.method,
        status="refunded",
        original_payment=payment,
        refund_reason=reason,
        notes=f"Refund for payment #{payment.pk}",
    )

    # Mark original as refunded
    payment.status = "refunded"
    payment.save(update_fields=["status"])

    payment.folio.recalculate()
    return refund
