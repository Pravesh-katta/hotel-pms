import os
from decimal import Decimal
from io import BytesIO

from django.template.loader import render_to_string

from .gst import amount_in_words


def generate_invoice_context(folio):
    """Build the full context dict for invoice rendering."""
    reservation = folio.reservation
    guest = reservation.guest
    hotel = folio.hotel

    charges = folio.charges.order_by("charge_date", "created_at")
    payments = folio.payments.filter(status="completed")

    # Separate GST totals
    total_cgst = sum(c.amount for c in charges if c.charge_type == "cgst")
    total_sgst = sum(c.amount for c in charges if c.charge_type == "sgst")
    total_igst = sum(c.amount for c in charges if c.charge_type == "igst")
    total_gst = total_cgst + total_sgst + total_igst

    # Get payment config
    try:
        payment_config = hotel.payment_config
        gst_number = payment_config.gst_number
        sac_code = payment_config.sac_code
    except Exception:
        gst_number = ""
        sac_code = "9963"

    # Get room info
    res_rooms = reservation.rooms.select_related("room", "room_type")

    return {
        "hotel": hotel,
        "guest": guest,
        "reservation": reservation,
        "folio": folio,
        "charges": charges,
        "payments": payments,
        "res_rooms": res_rooms,
        "total_cgst": total_cgst,
        "total_sgst": total_sgst,
        "total_igst": total_igst,
        "total_gst": total_gst,
        "gst_number": gst_number,
        "sac_code": sac_code,
        "amount_in_words": amount_in_words(folio.total_charges),
    }


def generate_invoice_html(folio):
    """Render invoice as HTML string."""
    context = generate_invoice_context(folio)
    return render_to_string("invoices/invoice.html", context)


def generate_invoice_pdf(folio):
    """
    Generate invoice PDF. Returns bytes.
    Uses xhtml2pdf if available, falls back to returning HTML.
    """
    html = generate_invoice_html(folio)

    try:
        from xhtml2pdf import pisa

        buffer = BytesIO()
        pisa_status = pisa.CreatePDF(html, dest=buffer)
        if pisa_status.err:
            return html.encode()
        buffer.seek(0)
        return buffer.read()
    except ImportError:
        return html.encode()
