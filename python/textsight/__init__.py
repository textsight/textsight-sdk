"""TextSight: free Python client for the TextSight AI detector and AI humanizer API."""

from .client import TextSight
from .errors import (
    APIError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    ServiceUnavailableError,
    TextSightError,
)

__version__ = "0.1.1"
__all__ = [
    "TextSight",
    "TextSightError",
    "APIError",
    "AuthenticationError",
    "PermissionDeniedError",
    "RateLimitError",
    "ServiceUnavailableError",
]
