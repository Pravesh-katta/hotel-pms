from django.shortcuts import redirect
from django.urls import reverse


class HotelMiddleware:
    """
    Sets request.hotel from the logged-in user's StaffProfile.
    - Super admin (hotel=None) gets request.hotel = None (sees all hotels).
    - Hotel staff gets request.hotel = their assigned hotel.
    - Anonymous users are redirected to login (except public paths).
    """

    PUBLIC_PATHS = [
        "/accounts/login/",
        "/superadmin/",
        "/health/",
        "/api/webhooks/",
        "/api/tasks/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for public paths
        for path in self.PUBLIC_PATHS:
            if request.path.startswith(path):
                request.hotel = None
                return self.get_response(request)

        # Skip for static/media
        if request.path.startswith("/static/") or request.path.startswith("/media/"):
            request.hotel = None
            return self.get_response(request)

        # Redirect anonymous users to login
        if not request.user.is_authenticated:
            request.hotel = None
            return redirect(f"{reverse('login')}?next={request.path}")

        # Set hotel from StaffProfile
        try:
            profile = request.user.staffprofile
            request.hotel = profile.hotel  # None for super_admin
        except Exception:
            request.hotel = None

        return self.get_response(request)
