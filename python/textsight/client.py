"""TextSight API client: AI content detection and AI text humanizing.

Docs: https://www.textsight.ai/api-docs.html
Get an API key: https://app.textsight.ai/signup
"""

from __future__ import annotations

import json
import os
import socket
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .errors import (
    APIError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    ServiceUnavailableError,
    TextSightError,
)

__all__ = ["TextSight"]

DEFAULT_BASE_URL = "https://api.textsight.ai/v2"
TONES = ("conversational", "professional", "academic", "blog", "email")
MAX_CHARS = 50_000


class TextSight:
    """Client for the TextSight API.

    >>> from textsight import TextSight
    >>> ts = TextSight()                      # reads TEXTSIGHT_API_KEY
    >>> ts.detect("Some text")["verdict"]
    'human'
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 60.0,
        max_retries: int = 2,
    ) -> None:
        self.api_key = api_key or os.environ.get("TEXTSIGHT_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "No API key. Pass api_key=... or set TEXTSIGHT_API_KEY. "
                "Get a key at https://app.textsight.ai/signup"
            )
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    # ---- public methods -------------------------------------------------

    def detect(self, text: str) -> Dict[str, Any]:
        """Detect AI-generated text with sentence-level scores.

        Returns keys: humanization_score (0-100, higher = more human),
        ai_probability (0-1), verdict ('human' | 'mixed' | 'ai'),
        sentences [{text, score, label}], confidence, model, request_id.
        """
        return self._post("/detect", {"text": _check_text(text)})

    def score(self, text: str) -> Dict[str, Any]:
        """Lightweight authenticity score (no sentence breakdown)."""
        return self._post("/score", {"text": _check_text(text)})

    def rewrite(
        self,
        text: str,
        *,
        tone: str = "conversational",
        strength: int = 3,
        preserve: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Humanize AI-sounding text.

        tone: conversational | professional | academic | blog | email
        strength: 1 (light) to 5 (aggressive)
        preserve: strings to keep unchanged (names, citations, numbers)
        """
        if tone not in TONES:
            raise ValueError(f"tone must be one of {TONES}")
        if isinstance(strength, bool) or not 1 <= int(strength) <= 5:
            raise ValueError("strength must be between 1 and 5")
        body: Dict[str, Any] = {
            "text": _check_text(text),
            "tone": tone,
            "strength": int(strength),
        }
        if preserve:
            if isinstance(preserve, str):
                preserve = [preserve]
            body["preserve"] = [str(p) for p in preserve]
        return self._post("/rewrite", body)

    humanize = rewrite  # alias

    # ---- internals ------------------------------------------------------

    def _post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        data = json.dumps(body).encode("utf-8")
        attempt = 0
        while True:
            req = urllib.request.Request(
                self.base_url + path,
                data=data,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "textsight-python/0.1.1",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    raw = resp.read().decode("utf-8")
                try:
                    return json.loads(raw or "{}")
                except ValueError:
                    raise APIError(
                        "Unexpected non-JSON response from TextSight API",
                        status=resp.status,
                        body=raw[:500],
                    ) from None
            except urllib.error.HTTPError as e:
                status = e.code
                payload = _read_json(e)
                retryable = status in (429, 500, 502, 503, 504)
                if retryable and attempt < self.max_retries:
                    time.sleep(_backoff(attempt, e.headers.get("Retry-After")))
                    attempt += 1
                    continue
                raise _error_for(status, payload) from None
            except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
                if attempt < self.max_retries:
                    time.sleep(_backoff(attempt, None))
                    attempt += 1
                    continue
                reason = getattr(e, "reason", e)
                raise TextSightError(f"Network error: {reason}") from None


def _check_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string")
    if len(text) > MAX_CHARS:
        raise ValueError(f"text is longer than {MAX_CHARS:,} characters")
    return text


def _read_json(e: urllib.error.HTTPError) -> Dict[str, Any]:
    try:
        return json.loads(e.read().decode("utf-8") or "{}")
    except Exception:
        return {}


def _backoff(attempt: int, retry_after: Optional[str]) -> float:
    if retry_after:
        try:
            return min(float(retry_after), 30.0)
        except ValueError:
            pass
    return min(0.5 * (2 ** attempt), 8.0)


def _error_for(status: int, payload: Dict[str, Any]) -> APIError:
    err = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(err, dict):
        code, message = err.get("code"), err.get("message")
    else:
        code, message = err, payload.get("message") if isinstance(payload, dict) else None
    message = message or f"HTTP {status}"
    cls = {
        401: AuthenticationError,
        403: PermissionDeniedError,
        429: RateLimitError,
        503: ServiceUnavailableError,
    }.get(status, APIError)
    return cls(message, status=status, code=code, body=payload)
