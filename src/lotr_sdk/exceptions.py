"""SDK exception types."""

from __future__ import annotations

from typing import Optional


class LOTRSDKError(Exception):
    """Base SDK exception."""


class AuthenticationError(LOTRSDKError):
    """Raised when API authentication fails."""


class APIRequestError(LOTRSDKError):
    """Raised for non-authentication API failures."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
