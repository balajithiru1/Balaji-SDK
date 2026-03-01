"""HTTP client for The One API."""

from __future__ import annotations

import random
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import urlencode

import requests

from .exceptions import APIRequestError, AuthenticationError
from .models import APIResponse
from .resources import MovieResource, QuoteResource


class LOTRClient:
    """Main entrypoint for the SDK.

    Args:
        api_key: The One API bearer token.
        base_url: Override for testing or self-hosted deployments.
        timeout: HTTP timeout in seconds.
        max_retries: Max retry attempts for transient failures.
        backoff_base_seconds: Base delay used for exponential backoff.
        max_backoff_seconds: Upper bound for retry delay.
        jitter_ratio: Random jitter ratio applied to backoff delays.
        event_hook: Optional callback for observability events.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://the-one-api.dev/v2",
        timeout: int = 15,
        max_retries: int = 3,
        backoff_base_seconds: float = 0.5,
        max_backoff_seconds: float = 8.0,
        jitter_ratio: float = 0.2,
        event_hook: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if backoff_base_seconds <= 0:
            raise ValueError("backoff_base_seconds must be > 0")
        if max_backoff_seconds <= 0:
            raise ValueError("max_backoff_seconds must be > 0")
        if jitter_ratio < 0:
            raise ValueError("jitter_ratio must be >= 0")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds
        self.max_backoff_seconds = max_backoff_seconds
        self.jitter_ratio = jitter_ratio
        self.event_hook = event_hook
        self.retryable_statuses: Set[int] = {408, 425, 429, 500, 502, 503, 504}
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Accept": "application/json",
                "User-Agent": "lotr-sdk-python/0.1.0",
            }
        )

        self.movies = MovieResource(self)
        self.quotes = QuoteResource(self)

    def get(
        self,
        path: str,
        *,
        params: Optional[Dict[str, str]] = None,
        filter_fragments: Optional[List[str]] = None,
    ) -> APIResponse:
        url = f"{self.base_url}{path}"
        query_parts: List[str] = []

        if params:
            query_parts.append(urlencode(params))
        if filter_fragments:
            query_parts.extend(filter_fragments)
        if query_parts:
            url = f"{url}?{'&'.join(query_parts)}"

        started_at = time.perf_counter()
        response, attempts = self._get_with_retry(url, path=path)
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        self._emit_event(
            "request_complete",
            {
                "path": path,
                "url": response.url or url,
                "status_code": response.status_code,
                "attempts": attempts,
                "elapsed_ms": elapsed_ms,
                "request_id": self._extract_request_id(response),
            },
        )
        return self._handle_response(response)

    def _get_with_retry(self, url: str, *, path: str) -> Tuple[requests.Response, int]:
        attempt = 0
        last_error: Optional[Exception] = None

        while attempt <= self.max_retries:
            self._emit_event(
                "request_attempt",
                {"path": path, "url": url, "attempt": attempt + 1, "max_attempts": self.max_retries + 1},
            )
            try:
                response = self.session.get(url, timeout=self.timeout)
            except (requests.Timeout, requests.ConnectionError) as exc:
                last_error = exc
                self._emit_event(
                    "request_exception",
                    {
                        "path": path,
                        "url": url,
                        "attempt": attempt + 1,
                        "error_type": exc.__class__.__name__,
                        "message": str(exc),
                    },
                )
                if attempt == self.max_retries:
                    raise APIRequestError(
                        "Request failed after retries due to network error"
                    ) from exc
                delay = self._compute_retry_delay(attempt=attempt, retry_after=None)
                self._emit_event(
                    "request_retry",
                    {
                        "path": path,
                        "url": url,
                        "attempt": attempt + 1,
                        "next_attempt": attempt + 2,
                        "reason": "network_error",
                        "sleep_seconds": round(delay, 3),
                    },
                )
                time.sleep(delay)
                attempt += 1
                continue

            if self._is_retryable_response(response) and attempt < self.max_retries:
                delay = self._compute_retry_delay(
                    attempt=attempt, retry_after=response.headers.get("Retry-After")
                )
                self._emit_event(
                    "request_retry",
                    {
                        "path": path,
                        "url": response.url or url,
                        "attempt": attempt + 1,
                        "next_attempt": attempt + 2,
                        "reason": "http_status",
                        "status_code": response.status_code,
                        "sleep_seconds": round(delay, 3),
                        "request_id": self._extract_request_id(response),
                    },
                )
                time.sleep(delay)
                attempt += 1
                continue

            return response, attempt + 1

        raise APIRequestError("Request failed after retries") from last_error

    def _compute_retry_delay(self, *, attempt: int, retry_after: Optional[str] = None) -> float:
        if retry_after is not None:
            try:
                retry_after_seconds = float(retry_after)
            except ValueError:
                retry_after_seconds = -1.0
            if retry_after_seconds >= 0:
                return min(retry_after_seconds, self.max_backoff_seconds)

        base_delay = min(
            self.backoff_base_seconds * (2 ** attempt),
            self.max_backoff_seconds,
        )
        jitter_delta = base_delay * self.jitter_ratio
        return max(0.0, base_delay + random.uniform(-jitter_delta, jitter_delta))

    def _is_retryable_response(self, response: requests.Response) -> bool:
        return response.status_code in self.retryable_statuses

    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        if self.event_hook is None:
            return
        event: Dict[str, Any] = {"type": event_type}
        event.update(payload)
        try:
            self.event_hook(event)
        except Exception:
            # Observability should never interfere with API behavior.
            return

    @staticmethod
    def _extract_request_id(response: requests.Response) -> Optional[str]:
        return response.headers.get("x-request-id") or response.headers.get("X-Request-Id")

    @staticmethod
    def _handle_response(response: requests.Response) -> APIResponse:
        if response.status_code in (401, 403):
            raise AuthenticationError("Authentication failed. Verify API token.")

        if response.status_code >= 400:
            try:
                payload = response.json()
                message = payload.get("message", response.text)
            except ValueError:
                message = response.text
            raise APIRequestError(message, status_code=response.status_code)

        data: Any = response.json()
        if not isinstance(data, dict) or "docs" not in data:
            raise APIRequestError("Unexpected API response format", status_code=response.status_code)

        return data
