from django.db import migrations


ROLE_MAP = {
    "hotel_admin": "hotel_admin",
    "manager": "manager",
    "front_desk": "front_desk",
    "housekeeping": "housekeeping",
}


def backfill_memberships(apps, schema_editor):
    StaffProfile = apps.get_model("accounts", "StaffProfile")
    HotelMembership = apps.get_model("accounts", "HotelMembership")

    for profile in StaffProfile.objects.select_related("hotel", "user").all():
        if profile.hotel_id is None:
            continue
        role = ROLE_MAP.get(profile.role)
        if role is None:
            continue
        HotelMembership.objects.get_or_create(
            user=profile.user,
            hotel=profile.hotel,
            defaults={"role": role, "is_active": profile.is_active},
        )


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_hotelmembership"),
        ("hotels", "0004_backfill_default_groups"),
    ]

    operations = [
        migrations.RunPython(backfill_memberships, reverse_noop),
    ]
