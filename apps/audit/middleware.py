from .signals import set_audit_context


class AuditMiddleware:
    """Store current user and IP in thread-local for audit logging."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
            if ip and "," in ip:
                ip = ip.split(",")[0].strip()
            set_audit_context(request.user, ip)
        else:
            set_audit_context(None, None)

        return self.get_response(request)
