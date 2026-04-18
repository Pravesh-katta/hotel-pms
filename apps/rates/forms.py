from django import forms
from django.forms import inlineformset_factory

from .models import RatePlan, RatePlanRate, SeasonalRate


class RatePlanForm(forms.ModelForm):
    class Meta:
        model = RatePlan
        fields = [
            "name", "plan_type", "source", "is_default", "is_active",
            "priority", "min_stay_nights", "cancellation_policy",
            "cancellation_hours", "cancellation_charge_percent",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "plan_type": forms.Select(attrs={"class": "form-select"}),
            "source": forms.Select(attrs={"class": "form-select"}),
            "priority": forms.NumberInput(attrs={"class": "form-control"}),
            "min_stay_nights": forms.NumberInput(attrs={"class": "form-control"}),
            "cancellation_policy": forms.Select(attrs={"class": "form-select"}),
            "cancellation_hours": forms.NumberInput(attrs={"class": "form-control"}),
            "cancellation_charge_percent": forms.NumberInput(attrs={"class": "form-control"}),
        }


class RatePlanRateForm(forms.ModelForm):
    class Meta:
        model = RatePlanRate
        fields = ["room_type", "base_rate", "extra_adult_rate", "extra_child_rate"]
        widgets = {
            "room_type": forms.Select(attrs={"class": "form-select"}),
            "base_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "extra_adult_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "extra_child_rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }


RatePlanRateFormSet = inlineformset_factory(
    RatePlan, RatePlanRate, form=RatePlanRateForm, extra=1, can_delete=True,
)


class SeasonalRateForm(forms.ModelForm):
    class Meta:
        model = SeasonalRate
        fields = ["name", "start_date", "end_date", "rate"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "rate": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
        }
