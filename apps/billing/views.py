from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render

from .models import Folio


@login_required
def folio_list(request):
    folios = Folio.objects.select_related("hotel", "reservation", "reservation__guest")
    if request.hotel:
        folios = folios.filter(hotel=request.hotel)

    status = request.GET.get("status", "")
    if status:
        folios = folios.filter(status=status)

    context = {
        "folios": folios[:100],
        "current_status": status,
    }
    return render(request, "dashboard/billing/folio_list.html", context)


@login_required
def folio_detail(request, pk):
    folio = get_object_or_404(
        Folio.objects.select_related("hotel", "reservation", "reservation__guest"), pk=pk
    )
    if request.hotel and folio.hotel != request.hotel:
        return HttpResponseForbidden()

    charges = folio.charges.all()
    payments = folio.payments.all()

    context = {
        "folio": folio,
        "charges": charges,
        "payments": payments,
    }
    return render(request, "dashboard/billing/folio_detail.html", context)
