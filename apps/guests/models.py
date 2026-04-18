from django.conf import settings
from django.db import models


class Guest(models.Model):
    ID_TYPE_CHOICES = [
        ("aadhar", "Aadhar Card"),
        ("passport", "Passport"),
        ("driving_license", "Driving License"),
        ("voter_id", "Voter ID"),
        ("other", "Other"),
    ]
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.CASCADE, related_name="guests")
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)
    id_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES, blank=True)
    id_number = models.CharField(max_length=50, blank=True)
    id_document_front = models.CharField(max_length=500, blank=True, help_text="Cloud Storage path")
    id_document_back = models.CharField(max_length=500, blank=True, help_text="Cloud Storage path")
    nationality = models.CharField(max_length=100, default="Indian")
    is_foreign = models.BooleanField(default=False)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=10, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if self.nationality and self.nationality.lower() != "indian":
            self.is_foreign = True
        super().save(*args, **kwargs)


class GuestVerification(models.Model):
    FORM_TYPE_CHOICES = [
        ("form_a", "Form A"),
        ("form_c", "Form C (Foreign Guest)"),
        ("police_intimation", "Police Intimation"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("submitted", "Submitted"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
    ]

    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name="verifications")
    reservation = models.ForeignKey(
        "reservations.Reservation", on_delete=models.CASCADE, related_name="verifications"
    )
    hotel = models.ForeignKey("hotels.Hotel", on_delete=models.CASCADE, related_name="guest_verifications")
    form_type = models.CharField(max_length=20, choices=FORM_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    submission_date = models.DateField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    verified_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.guest.full_name} — {self.get_form_type_display()} ({self.get_status_display()})"
