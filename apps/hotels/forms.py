from django import forms

from .models import Hotel, OTAConnection


class HotelCreateForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = [
            "name", "code", "address", "city", "state", "country",
            "phone", "email", "currency", "timezone", "max_rooms",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. MUM02"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control"}),
            "country": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "currency": forms.TextInput(attrs={"class": "form-control"}),
            "timezone": forms.TextInput(attrs={"class": "form-control"}),
            "max_rooms": forms.NumberInput(attrs={"class": "form-control"}),
        }


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
