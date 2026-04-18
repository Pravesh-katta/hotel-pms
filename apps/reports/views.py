import csv
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render

from apps.accounts.decorators import role_required
from apps.audit.models import DailyAuditSnapshot
from apps.billing.models import Folio, FolioCharge
from apps.hotels.models import Hotel
from apps.payments.models import Payment


@login_required
@role_required("hotel_admin", "manager")
def sales_report(request):
    """Sales report with date range filters."""
    start_str = request.GET.get("start", "")
    end_str = request.GET.get("end", "")

    try:
        start_date = date.fromisoformat(start_str)
    except (ValueError, TypeError):
        start_date = date.today().replace(day=1)

    try:
        end_date = date.fromisoformat(end_str)
    except (ValueError, TypeError):
        end_date = date.today()

    hotel = request.hotel

    # Revenue (charges excl. discount)
    charges_qs = FolioCharge.objects.filter(
        charge_date__gte=start_date,
        charge_date__lte=end_date,
    ).exclude(charge_type="discount")
    if hotel:
        charges_qs = charges_qs.filter(folio__hotel=hotel)

    total_revenue = charges_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    # GST
    gst_qs = charges_qs.filter(charge_type__in=["cgst", "sgst", "igst"])
    total_gst = gst_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    # Collections
    payments_qs = Payment.objects.filter(
        status="completed",
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )
    if hotel:
        payments_qs = payments_qs.filter(hotel=hotel)

    total_collected = payments_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    # By payment method
    by_method = payments_qs.values("method").annotate(total=Sum("amount")).order_by("-total")

    # Per hotel breakdown (for super admin)
    hotel_breakdown = []
    if not hotel:
        for h in Hotel.objects.filter(is_active=True):
            h_charges = charges_qs.filter(folio__hotel=h).aggregate(total=Sum("amount"))["total"] or 0
            h_collected = payments_qs.filter(hotel=h).aggregate(total=Sum("amount"))["total"] or 0
            hotel_breakdown.append({
                "hotel": h,
                "revenue": h_charges,
                "collected": h_collected,
                "outstanding": h_charges - h_collected,
            })

    context = {
        "start_date": start_date,
        "end_date": end_date,
        "total_revenue": total_revenue,
        "total_gst": total_gst,
        "total_collected": total_collected,
        "outstanding": total_revenue - total_collected,
        "by_method": by_method,
        "hotel_breakdown": hotel_breakdown,
    }
    return render(request, "dashboard/reports/sales.html", context)


@login_required
@role_required("hotel_admin", "manager")
def occupancy_report(request):
    """Occupancy report from DailyAuditSnapshot."""
    hotel = request.hotel
    snapshots = DailyAuditSnapshot.objects.order_by("-audit_date")[:30]
    if hotel:
        snapshots = snapshots.filter(hotel=hotel)

    context = {"snapshots": snapshots}
    return render(request, "dashboard/reports/occupancy.html", context)


@login_required
@role_required("hotel_admin", "manager")
def gst_report(request):
    """GST report for filing — CGST/SGST breakup per folio."""
    start_str = request.GET.get("start", "")
    end_str = request.GET.get("end", "")

    try:
        start_date = date.fromisoformat(start_str)
    except (ValueError, TypeError):
        start_date = date.today().replace(day=1)

    try:
        end_date = date.fromisoformat(end_str)
    except (ValueError, TypeError):
        end_date = date.today()

    hotel = request.hotel
    folios = Folio.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    ).select_related("reservation", "reservation__guest", "hotel")
    if hotel:
        folios = folios.filter(hotel=hotel)

    folio_data = []
    for folio in folios:
        cgst = folio.charges.filter(charge_type="cgst").aggregate(t=Sum("amount"))["t"] or 0
        sgst = folio.charges.filter(charge_type="sgst").aggregate(t=Sum("amount"))["t"] or 0
        room = folio.charges.filter(charge_type="room_charge").aggregate(t=Sum("amount"))["t"] or 0
        folio_data.append({
            "folio": folio,
            "room_charges": room,
            "cgst": cgst,
            "sgst": sgst,
            "total": room + cgst + sgst,
        })

    context = {
        "folio_data": folio_data,
        "start_date": start_date,
        "end_date": end_date,
    }
    return render(request, "dashboard/reports/gst.html", context)


@login_required
@role_required("hotel_admin", "manager")
def export_sales_csv(request):
    """Export sales data as CSV."""
    start = request.GET.get("start", str(date.today().replace(day=1)))
    end = request.GET.get("end", str(date.today()))

    hotel = request.hotel
    payments = Payment.objects.filter(
        status="completed",
        created_at__date__gte=start,
        created_at__date__lte=end,
    ).select_related("folio", "folio__reservation", "folio__reservation__guest", "hotel")
    if hotel:
        payments = payments.filter(hotel=hotel)

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="sales_{start}_to_{end}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Date", "Hotel", "Folio #", "Guest", "Method", "Amount", "Reference"])
    for p in payments:
        writer.writerow([
            p.created_at.strftime("%Y-%m-%d"),
            p.hotel.name,
            p.folio.folio_number,
            p.folio.reservation.guest.full_name,
            p.get_method_display(),
            p.amount,
            p.razorpay_payment_id or p.reference_number or "",
        ])

    return response
