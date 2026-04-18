from django import forms

from apps.guests.models import Guest
from apps.rooms.models import Room, RoomType


class ReservationCreateForm(forms.Form):
    guest = forms.ModelChoiceField(
        queryset=Guest.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    room_type = forms.ModelChoiceField(
        queryset=RoomType.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    room = forms.ModelChoiceField(
        queryset=Room.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    check_in_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )
    check_out_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )
    source = forms.ChoiceField(
        choices=[
            ("walk_in", "Walk-in"),
            ("phone", "Phone"),
            ("website", "Website"),
            ("airbnb", "Airbnb"),
            ("booking_com", "Booking.com"),
            ("ota_other", "Other OTA"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    num_adults = forms.IntegerField(
        initial=1, min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    num_children = forms.IntegerField(
        initial=0, min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    special_requests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    def __init__(self, hotel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hotel:
            self.fields["guest"].queryset = Guest.objects.filter(hotel=hotel)
            self.fields["room_type"].queryset = RoomType.objects.filter(hotel=hotel)
            self.fields["room"].queryset = Room.objects.filter(hotel=hotel, is_active=True)
        else:
            self.fields["guest"].queryset = Guest.objects.all()
            self.fields["room_type"].queryset = RoomType.objects.all()
            self.fields["room"].queryset = Room.objects.filter(is_active=True)

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get("check_in_date")
        check_out = cleaned.get("check_out_date")
        if check_in and check_out and check_out <= check_in:
            raise forms.ValidationError("Check-out date must be after check-in date.")
        return cleaned


class ReservationEditForm(forms.Form):
    """Form for modifying an existing reservation — extend/shorten stay, change room, etc."""
    check_out_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        help_text="Change check-out date to extend or shorten the stay",
    )
    room = forms.ModelChoiceField(
        queryset=Room.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        help_text="Change room assignment",
    )
    num_adults = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    num_children = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    special_requests = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    def __init__(self, reservation, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hotel = reservation.hotel
        self.fields["room"].queryset = Room.objects.filter(
            hotel=hotel, is_active=True
        ).select_related("room_type")

        # Pre-fill current values
        res_room = reservation.rooms.first()
        if not self.is_bound:
            self.initial["check_out_date"] = reservation.check_out_date
            self.initial["num_adults"] = reservation.num_adults
            self.initial["num_children"] = reservation.num_children
            self.initial["special_requests"] = reservation.special_requests
            if res_room:
                self.initial["room"] = res_room.room_id

    def clean_check_out_date(self):
        check_out = self.cleaned_data["check_out_date"]
        return check_out


class WalkInForm(forms.Form):
    """Simplified form for walk-in guests — guest details + room selection."""
    first_name = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    last_name = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    phone = forms.CharField(
        max_length=20, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    id_type = forms.ChoiceField(
        choices=[("", "---")] + list(Guest.ID_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    id_number = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    nationality = forms.CharField(
        max_length=100, initial="Indian",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    room = forms.ModelChoiceField(
        queryset=Room.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    nights = forms.IntegerField(
        initial=1, min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    num_adults = forms.IntegerField(
        initial=1, min_value=1,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )

    def __init__(self, hotel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hotel:
            self.fields["room"].queryset = Room.objects.filter(
                hotel=hotel, is_active=True, status="available"
            ).select_related("room_type")
