from django.utils.cache import patch_cache_control


class ContentSecurityPolicyMiddleware:
    """Restricts external resources to the hosts the app actually loads from
    (Google Fonts; Chart.js is served locally) instead of allowing any origin.

    Inline <style>/<script> blocks are still allowed ('unsafe-inline') —
    templates use plenty of both, and moving to nonces/hashes for every one
    of them would be a much larger refactor than this warrants right now.
    This still blocks the main risk a missing CSP leaves open: a script tag
    injected from an attacker-controlled domain.
    """

    POLICY = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "script-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'self'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Content-Security-Policy"] = self.POLICY
        return response



class PrivatePagesNoStoreMiddleware:
    """Pages for a signed-in user hold their journal, so browsers and proxies
    must not keep a copy (the Back button after logout would show it)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and "Cache-Control" not in response:
            patch_cache_control(response, private=True, no_store=True, max_age=0)
        return response
