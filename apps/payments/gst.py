from decimal import Decimal, ROUND_HALF_UP


def get_gst_rate(room_rate):
    """Returns GST percentage based on room tariff slab."""
    if room_rate > Decimal("7500"):
        return Decimal("18")
    return Decimal("12")


def calculate_gst(room_rate):
    """
    Calculate GST breakup for a room rate.
    Returns dict with cgst, sgst, total_gst, and grand_total.
    """
    gst_rate = get_gst_rate(room_rate)
    total_gst = (room_rate * gst_rate / Decimal("100")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    half_gst = (total_gst / 2).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    return {
        "gst_rate": gst_rate,
        "cgst_rate": gst_rate / 2,
        "sgst_rate": gst_rate / 2,
        "cgst": half_gst,
        "sgst": half_gst,
        "total_gst": total_gst,
        "grand_total": room_rate + total_gst,
    }


def amount_in_words(amount):
    """Convert amount to Indian English words for invoice."""
    ones = [
        "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
        "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
        "Seventeen", "Eighteen", "Nineteen",
    ]
    tens = [
        "", "", "Twenty", "Thirty", "Forty", "Fifty",
        "Sixty", "Seventy", "Eighty", "Ninety",
    ]

    def _convert(n):
        if n < 20:
            return ones[n]
        if n < 100:
            return tens[n // 10] + (" " + ones[n % 10] if n % 10 else "")
        if n < 1000:
            return ones[n // 100] + " Hundred" + (" and " + _convert(n % 100) if n % 100 else "")
        if n < 100000:
            return _convert(n // 1000) + " Thousand" + (" " + _convert(n % 1000) if n % 1000 else "")
        if n < 10000000:
            return _convert(n // 100000) + " Lakh" + (" " + _convert(n % 100000) if n % 100000 else "")
        return _convert(n // 10000000) + " Crore" + (" " + _convert(n % 10000000) if n % 10000000 else "")

    amt = int(amount)
    paise = int(round((amount - amt) * 100))

    words = "Rupees " + _convert(amt)
    if paise:
        words += " and " + _convert(paise) + " Paise"
    words += " Only"
    return words
