"""Type aliases for API response payloads."""

from __future__ import annotations

from typing import Any, TypedDict


class APIResponse(TypedDict):
    docs: list[dict[str, Any]]
    total: int
    limit: int
    offset: int
    page: int
    pages: int


Movie = dict[str, Any]
Quote = dict[str, Any]
