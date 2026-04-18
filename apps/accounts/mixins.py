from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class HotelScopedMixin(LoginRequiredMixin):
    """
    Mixin for class-based views that automatically filters querysets by hotel.
    Super admin (request.hotel=None) sees all data.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.hotel is not None:
            qs = qs.filter(hotel=self.request.hotel)
        return qs

    def get_hotel(self):
        return self.request.hotel


class RoleRequiredMixin:
    """
    Mixin that restricts access to specific roles.
    Usage: allowed_roles = ["super_admin", "hotel_admin", "manager"]
    """

    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        try:
            profile = request.user.staffprofile
        except Exception:
            raise PermissionDenied("No staff profile found.")

        if profile.is_super_admin:
            return super().dispatch(request, *args, **kwargs)

        if profile.role not in self.allowed_roles:
            raise PermissionDenied("You do not have permission to access this page.")

        return super().dispatch(request, *args, **kwargs)
