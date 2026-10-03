import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    Middleware to log incoming HTTP requests including HTTP method, path,
    and the authenticated or anonymous user making the request.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        username = user.username if user and user.is_authenticated else 'AnonymousUser'
        logger.info(f"[REQUEST] {request.method} {request.path} | User: {username}")

        response = self.get_response(request)

        logger.info(f"[RESPONSE] {request.method} {request.path} -> Status {response.status_code}")
        return response
