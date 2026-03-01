from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import requests

from lotr_sdk import LOTRClient


def _response(
    status: int,
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> requests.Response:
    r = requests.Response()
    r.status_code = status
    r._content = json.dumps(
        payload or {"docs": [], "total": 0, "limit": 1, "offset": 0, "page": 1, "pages": 1}
    ).encode("utf-8")
    r.headers = headers or {}
    r.url = "https://example.test/v2/movie"
    return r


def test_emits_retry_and_completion_events(monkeypatch) -> None:
    events: List[Dict[str, Any]] = []

    client = LOTRClient(
        "token",
        base_url="https://example.test/v2",
        max_retries=2,
        event_hook=events.append,
    )

    responses = [_response(503, {"message": "service unavailable"}), _response(200)]
    monkeypatch.setattr(client.session, "get", lambda url, timeout: responses.pop(0))
    monkeypatch.setattr("lotr_sdk.client.time.sleep", lambda s: None)
    monkeypatch.setattr("lotr_sdk.client.random.uniform", lambda a, b: 0.0)

    client.movies.list(limit=1)

    types = [event["type"] for event in events]
    assert "request_attempt" in types
    assert "request_retry" in types
    assert "request_complete" in types

    completion = [event for event in events if event["type"] == "request_complete"][0]
    assert completion["status_code"] == 200
    assert completion["attempts"] == 2
    assert "elapsed_ms" in completion


def test_event_hook_errors_are_ignored(monkeypatch) -> None:
    def bad_hook(event: Dict[str, Any]) -> None:
        raise RuntimeError("boom")

    client = LOTRClient(
        "token",
        base_url="https://example.test/v2",
        max_retries=0,
        event_hook=bad_hook,
    )

    monkeypatch.setattr(client.session, "get", lambda url, timeout: _response(200))

    payload = client.movies.list(limit=1)
    assert payload["docs"] == []
