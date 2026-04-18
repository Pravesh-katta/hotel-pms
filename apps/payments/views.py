import os
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.billing.models import Folio

from .invoice import generate_invoice_pdf
from .models import Payment
from .services import (
    create_razorpay_order,
    process_refund,
    record_bank_transfer,
    record_cash_payment,
)


@login_required
def payment_page(request, folio_pk):
    """Show Razorpay checkout page for online payment."""
    folio = get_object_or_404(Folio, pk=folio_pk)
    if request.hotel and folio.hotel != request.hotel:
        return HttpResponseForbidden()

    amount = folio.balance
    if amount <= 0:
        messages.info(request, "No balance due.")
        return redirect("folio_detail", pk=folio.pk)

    razorpay_key = os.environ.get("RAZORPAY_KEY_ID", "")

    # Try to get hotel-specific key
    try:
        if folio.hotel.payment_config.razorpay_key_id:
            razorpay_key = folio.hotel.payment_config.razorpay_key_id
    except Exception:
        pass

    razorpay_order = None
    payment = None

    if razorpay_key:
        try:
            payment, razorpay_order = create_razorpay_order(folio, amount)
        except Exception as e:
            messages.warning(request, f"Razorpay unavailable: {e}. Use cash payment instead.")

    context = {
        "folio": folio,
        "amount": amount,
        "amount_paise": int(amount * 100),
        "razorpay_key": razorpay_key,
        "razorpay_order": razorpay_order,
        "payment": payment,
    }
    return render(request, "dashboard/billing/payment_page.html", context)


@login_required
def payment_callback(request, folio_pk):
    """Handle Razorpay payment callback (POST from checkout.js)."""
    folio = get_object_or_404(Folio, pk=folio_pk)

    if request.method == "POST":
        from .services import verify_razorpay_payment

        try:
            verify_razorpay_payment(
                razorpay_order_id=request.POST.get("razorpay_order_id", ""),
                razorpay_payment_id=request.POST.get("razorpay_payment_id", ""),
                razorpay_signature=request.POST.get("razorpay_signature", ""),
            )
            messages.success(request, "Payment received successfully!")
        except Exception as e:
            messages.error(request, f"Payment verification failed: {e}")

    return redirect("folio_detail", pk=folio.pk)


@login_required
def cash_payment(request, folio_pk):
    """Record a cash or bank transfer payment."""
    folio = get_object_or_404(Folio, pk=folio_pk)
    if request.hotel and folio.hotel != request.hotel:
        return HttpResponseForbidden()

    if request.method == "POST":
        amount = request.POST.get("amount", "0")
        method = request.POST.get("method", "cash")
        reference = request.POST.get("reference_number", "")
        notes = request.POST.get("notes", "")

        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")

            if method == "bank_transfer":
                record_bank_transfer(folio, amount, reference, request.user, notes)
            else:
                record_cash_payment(folio, amount, request.user, reference, notes)

            messages.success(request, f"Payment of ₹{amount} recorded.")
            return redirect("folio_detail", pk=folio.pk)
        except (ValueError, Exception) as e:
            messages.error(request, str(e))

    context = {"folio": folio, "balance": folio.balance}
    return render(request, "dashboard/billing/cash_payment.html", context)


@login_required
def refund_view(request, folio_pk):
    """Process a refund."""
    folio = get_object_or_404(Folio, pk=folio_pk)
    if request.hotel and folio.hotel != request.hotel:
        return HttpResponseForbidden()

    completed_payments = folio.payments.filter(status="completed")

    if request.method == "POST":
        payment_id = request.POST.get("payment_id")
        amount = request.POST.get("amount", "0")
        reason = request.POST.get("reason", "")

        try:
            payment = Payment.objects.get(pk=payment_id, folio=folio)
            process_refund(payment, Decimal(amount), reason)
            messages.success(request, f"Refund of ₹{amount} processed.")
            return redirect("folio_detail", pk=folio.pk)
        except (Payment.DoesNotExist, ValueError) as e:
            messages.error(request, str(e))

    context = {"folio": folio, "payments": completed_payments}
    return render(request, "dashboard/billing/refund.html", context)


@login_required
def invoice_download(request, folio_pk):
    """Download invoice as PDF."""
    folio = get_object_or_404(
        Folio.objects.select_related("hotel", "reservation", "reservation__guest"),
        pk=folio_pk,
    )
    if request.hotel and folio.hotel != request.hotel:
        return HttpResponseForbidden()

    pdf_bytes = generate_invoice_pdf(folio)

    if pdf_bytes[:5] == b"<!DOC" or pdf_bytes[:5] == b"<html":
        response = HttpResponse(pdf_bytes, content_type="text/html")
    else:
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="Invoice-{folio.folio_number}.pdf"'

    return response
