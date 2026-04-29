from django.db import migrations
from django.utils.text import slugify


def create_default_group_per_hotel(apps, schema_editor):
    HotelGroup = apps.get_model("hotels", "HotelGroup")
    Hotel = apps.get_model("hotels", "Hotel")

    if not Hotel.objects.exists():
        return

    default_group, _ = HotelGroup.objects.get_or_create(
        slug="default",
        defaults={"name": "Default Group", "is_active": True},
    )

    Hotel.objects.filter(group__isnull=True).update(group=default_group)


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("hotels", "0003_hotelgroup_hotel_group"),
    ]

    operations = [
        migrations.RunPython(create_default_group_per_hotel, reverse_noop),
    ]
