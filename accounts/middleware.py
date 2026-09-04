from django.shortcuts import redirect
from django.urls import Resolver404, resolve

from .services import user_must_change_password

EXEMPT_URL_NAMES = {"password_change", "password_change_done", "logout"}


class ForcePasswordChangeMiddleware:
    """Sends a login still on its guarded-service default password straight to
    the change-password form before it can reach anything else."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user_must_change_password(user):
            try:
                url_name = resolve(request.path_info).url_name
            except Resolver404:
                url_name = None
            if url_name not in EXEMPT_URL_NAMES:
                return redirect("password_change")
        return self.get_response(request)
