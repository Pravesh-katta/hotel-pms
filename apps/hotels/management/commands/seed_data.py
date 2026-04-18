from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.accounts.models import StaffProfile
from apps.hotels.models import Hotel
from apps.notifications.models import NotificationPreference
from apps.payments.models import HotelPaymentConfig
from apps.rates.models import RatePlan, RatePlanRate
from apps.rooms.models import Room, RoomType


class Command(BaseCommand):
    help = "Seed database with a test hotel, rooms, rate plans, and staff users"

    def handle(self, *args, **options):
        if Hotel.objects.exists():
            self.stdout.write(self.style.WARNING("Data already exists. Skipping seed."))
            return

        # Create hotel
        hotel = Hotel.objects.create(
            name="Mumbai Seaside Hotel",
            code="MUM01",
            address="123 Marine Drive",
            city="Mumbai",
            state="Maharashtra",
            country="India",
            phone="+91 22 1234 5678",
            email="info@mumbaiseaside.com",
            max_rooms=15,
        )
        self.stdout.write(f"Created hotel: {hotel}")

        # Create room types
        standard = RoomType.objects.create(
            hotel=hotel, name="Standard", description="Standard room with city view",
            base_rate=Decimal("1500.00"), max_occupancy=2,
        )
        deluxe = RoomType.objects.create(
            hotel=hotel, name="Deluxe", description="Deluxe room with sea view",
            base_rate=Decimal("2500.00"), max_occupancy=3,
        )
        suite = RoomType.objects.create(
            hotel=hotel, name="Suite", description="Luxury suite with living area",
            base_rate=Decimal("4000.00"), max_occupancy=4,
        )
        self.stdout.write(f"Created room types: Standard, Deluxe, Suite")

        # Create 13 rooms
        rooms_config = [
            # 5 Standard rooms
            ("101", "1", standard), ("102", "1", standard), ("103", "1", standard),
            ("104", "1", standard), ("105", "1", standard),
            # 5 Deluxe rooms
            ("201", "2", deluxe), ("202", "2", deluxe), ("203", "2", deluxe),
            ("204", "2", deluxe), ("205", "2", deluxe),
            # 3 Suites
            ("301", "3", suite), ("302", "3", suite), ("303", "3", suite),
        ]
        for room_number, floor, room_type in rooms_config:
            Room.objects.create(
                hotel=hotel, room_type=room_type,
                room_number=room_number, floor=floor,
            )
        self.stdout.write(f"Created {len(rooms_config)} rooms")

        # Create default rate plan
        rate_plan = RatePlan.objects.create(
            hotel=hotel, name="Standard Rate", plan_type="standard",
            is_default=True, priority=0, cancellation_policy="moderate",
            cancellation_hours=24, cancellation_charge_percent=Decimal("100.00"),
        )
        RatePlanRate.objects.create(
            rate_plan=rate_plan, room_type=standard,
            base_rate=Decimal("1500.00"), extra_adult_rate=Decimal("500.00"),
        )
        RatePlanRate.objects.create(
            rate_plan=rate_plan, room_type=deluxe,
            base_rate=Decimal("2500.00"), extra_adult_rate=Decimal("600.00"),
        )
        RatePlanRate.objects.create(
            rate_plan=rate_plan, room_type=suite,
            base_rate=Decimal("4000.00"), extra_adult_rate=Decimal("800.00"),
        )
        self.stdout.write(f"Created rate plan: {rate_plan}")

        # Create payment config
        HotelPaymentConfig.objects.create(
            hotel=hotel, gst_number="27AABCU9603R1ZM", gst_rate=Decimal("12.00"),
        )

        # Create notification preferences
        NotificationPreference.objects.create(hotel=hotel)

        # Create super admin user
        admin_user = User.objects.create_superuser(
            username="admin", email="admin@hotelpms.com", password="admin123",
            first_name="System", last_name="Admin",
        )
        StaffProfile.objects.create(user=admin_user, hotel=None, role="super_admin")
        self.stdout.write(f"Created super admin: admin / admin123")

        # Create hotel manager
        manager_user = User.objects.create_user(
            username="manager", email="manager@mumbaiseaside.com", password="manager123",
            first_name="Rahul", last_name="Sharma",
        )
        StaffProfile.objects.create(user=manager_user, hotel=hotel, role="manager")
        self.stdout.write(f"Created manager: manager / manager123")

        # Create front desk user
        fd_user = User.objects.create_user(
            username="frontdesk", email="frontdesk@mumbaiseaside.com", password="frontdesk123",
            first_name="Priya", last_name="Patel",
        )
        StaffProfile.objects.create(user=fd_user, hotel=hotel, role="front_desk")
        self.stdout.write(f"Created front desk: frontdesk / frontdesk123")

        self.stdout.write(self.style.SUCCESS("\nSeed data created successfully!"))
        self.stdout.write(self.style.SUCCESS("Login at /superadmin/ with admin / admin123"))
