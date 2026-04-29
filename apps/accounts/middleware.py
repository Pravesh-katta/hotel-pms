from django.shortcuts import redirect
from django.urls import reverse

from apps.hotels.models import Hotel


class HotelMiddleware:
    """
    Sets request.hotel based on the logged-in user's session selection.

    - Super admin: can access any hotel. If nothing selected, request.hotel = None.
    - Hotel staff: request.hotel comes from session["active_hotel_id"],
      scoped to the hotels they have a HotelMembership for.
    - Anonymous users are redirected to login (except public paths).
    - If a staff user hits a /dashboard/ URL without having picked a hotel,
      they are bounced to the group dashboard so they can choose one.
    """

    PUBLIC_PATHS = [
        "/accounts/login/",
        "/superadmin/",
        "/health/",
        "/api/webhooks/",
        "/api/tasks/",
        "/hotel-dashboard/",
    ]

    SESSION_KEY = "active_hotel_id"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        for path in self.PUBLIC_PATHS:
            if request.path.startswith(path):
                request.hotel = self._resolve_hotel(request) if request.user.is_authenticated else None
                return self.get_response(request)

        if request.path.startswith("/static/") or request.path.startswith("/media/"):
            request.hotel = None
            return self.get_response(request)

        if not request.user.is_authenticated:
            request.hotel = None
            return redirect(f"{reverse('login')}?next={request.path}")

        request.hotel = self._resolve_hotel(request)

        profile = getattr(request.user, "staffprofile", None)
        is_super = profile and profile.is_super_admin

        if request.hotel is None and not is_super and request.path.startswith("/dashboard"):
            return redirect(reverse("group_dashboard"))

        return self.get_response(request)

    def _resolve_hotel(self, request):
        hotel_id = request.session.get(self.SESSION_KEY)
        if not hotel_id:
            return None

        profile = getattr(request.user, "staffprofile", None)
        is_super = profile and profile.is_super_admin

        qs = Hotel.objects.filter(id=hotel_id)
        if not is_super:
            qs = qs.filter(memberships__user=request.user, memberships__is_active=True)

        hotel = qs.first()
        if hotel is None:
            request.session.pop(self.SESSION_KEY, None)
        return hotel
