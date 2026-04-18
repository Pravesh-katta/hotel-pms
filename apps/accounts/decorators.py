from functools import wraps

from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """
    Decorator for function-based views that restricts access to specific roles.
    Super admin always has access.
    Usage: @role_required("front_desk", "manager", "hotel_admin")
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                raise PermissionDenied

            try:
                profile = request.user.staffprofile
            except Exception:
                raise PermissionDenied("No staff profile found.")

            if profile.is_super_admin:
                return view_func(request, *args, **kwargs)

            if profile.role not in roles:
                raise PermissionDenied("You do not have permission to access this page.")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator
