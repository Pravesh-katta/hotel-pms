from django import forms

from .models import OTAConnection


class OTAConnectionForm(forms.ModelForm):
    class Meta:
        model = OTAConnection
        fields = [
            "channel", "connection_type", "channel_manager_name",
            "external_property_id", "api_key_id", "ical_url",
            "sync_bookings", "sync_rates", "sync_availability",
            "is_active", "notes",
        ]
        widgets = {
            "channel": forms.Select(attrs={"class": "form-select"}),
            "connection_type": forms.Select(attrs={"class": "form-select"}),
            "channel_manager_name": forms.TextInput(attrs={"class": "form-control"}),
            "external_property_id": forms.TextInput(attrs={"class": "form-control"}),
            "api_key_id": forms.TextInput(attrs={"class": "form-control"}),
            "ical_url": forms.URLInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
