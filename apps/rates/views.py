from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.decorators import role_required

from .forms import RatePlanForm, RatePlanRateFormSet, SeasonalRateForm
from .models import RatePlan, RatePlanRate, SeasonalRate


@login_required
@role_required("hotel_admin", "manager")
def rate_plan_list(request):
    plans = RatePlan.objects.prefetch_related("rates__room_type")
    if request.hotel:
        plans = plans.filter(hotel=request.hotel)

    context = {"plans": plans}
    return render(request, "dashboard/rates/list.html", context)


@login_required
@role_required("hotel_admin", "manager")
def rate_plan_create(request):
    if request.method == "POST":
        form = RatePlanForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            if request.hotel:
                plan.hotel = request.hotel
            plan.save()
            messages.success(request, f"Rate plan '{plan.name}' created. Now set room prices.")
            return redirect("rate_plan_edit", pk=plan.pk)
    else:
        form = RatePlanForm()

    return render(request, "dashboard/rates/form.html", {"form": form, "title": "New Rate Plan"})


@login_required
@role_required("hotel_admin", "manager")
def rate_plan_edit(request, pk):
    plan = get_object_or_404(RatePlan, pk=pk)
    if request.hotel and plan.hotel != request.hotel:
        return HttpResponseForbidden()

    if request.method == "POST":
        form = RatePlanForm(request.POST, instance=plan)
        formset = RatePlanRateFormSet(request.POST, instance=plan)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, f"Rate plan '{plan.name}' updated.")
            return redirect("rate_plan_list")
    else:
        form = RatePlanForm(instance=plan)
        formset = RatePlanRateFormSet(instance=plan)

    context = {
        "form": form,
        "formset": formset,
        "plan": plan,
        "title": f"Edit: {plan.name}",
    }
    return render(request, "dashboard/rates/edit.html", context)


@login_required
@role_required("hotel_admin", "manager")
def seasonal_rate_manage(request, rate_plan_rate_pk):
    rpr = get_object_or_404(RatePlanRate, pk=rate_plan_rate_pk)
    if request.hotel and rpr.rate_plan.hotel != request.hotel:
        return HttpResponseForbidden()

    if request.method == "POST":
        form = SeasonalRateForm(request.POST)
        if form.is_valid():
            seasonal = form.save(commit=False)
            seasonal.rate_plan_rate = rpr
            seasonal.save()
            messages.success(request, f"Seasonal rate '{seasonal.name}' added.")
            return redirect("rate_plan_edit", pk=rpr.rate_plan.pk)
    else:
        form = SeasonalRateForm()

    seasonals = rpr.seasonal_rates.all()
    context = {
        "form": form,
        "rpr": rpr,
        "seasonals": seasonals,
    }
    return render(request, "dashboard/rates/seasonal.html", context)
