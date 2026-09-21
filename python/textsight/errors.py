from typing import Any, Optional


class TextSightError(Exception):
    """Base error for the TextSight client."""


class APIError(TextSightError):
    def __init__(
        self,
        message: str,
        *,
        status: Optional[int] = None,
        code: Optional[str] = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.body = body


class AuthenticationError(APIError):
    """401: missing or invalid API key."""


class PermissionDeniedError(APIError):
    """403: no API access on your plan, missing scope, or quota used up."""


class RateLimitError(APIError):
    """429: too many requests per minute."""


class ServiceUnavailableError(APIError):
    """503: detector temporarily unavailable, safe to retry."""
