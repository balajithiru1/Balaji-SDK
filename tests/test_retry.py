from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import pytest
import requests

from lotr_sdk import LOTRClient
from lotr_sdk.exceptions import APIRequestError, AuthenticationError


def _response(
    status: int,
    payload: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> requests.Response:
    r = requests.Response()
    r.status_code = status
    r._content = json.dumps(payload or {"docs": [], "total": 0, "limit": 1, "offset": 0, "page": 1, "pages": 1}).encode("utf-8")
    r.headers = headers or {}
    r.url = "https://example.test/v2/movie"
    return r


def test_retries_on_transient_status_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    client = LOTRClient("token", base_url="https://example.test/v2", max_retries=3)

    calls: List[int] = []
    sleeps: List[float] = []
    responses = [_response(500, {"message": "oops"}), _response(503, {"message": "oops"}), _response(200)]

    def fake_get(url: str, timeout: int) -> requests.Response:
        calls.append(timeout)
        return responses.pop(0)

    monkeypatch.setattr(client.session, "get", fake_get)
    monkeypatch.setattr("lotr_sdk.client.time.sleep", lambda s: sleeps.append(s))
    monkeypatch.setattr("lotr_sdk.client.random.uniform", lambda a, b: 0.0)

    payload = client.movies.list()

    assert payload["docs"] == []
    assert len(calls) == 3
    assert len(sleeps) == 2


def test_uses_retry_after_header(monkeypatch: pytest.MonkeyPatch) -> None:
    client = LOTRClient("token", base_url="https://example.test/v2", max_retries=1)

    sleeps: List[float] = []
    responses = [_response(429, {"message": "rate"}, headers={"Retry-After": "1.5"}), _response(200)]

    monkeypatch.setattr(client.session, "get", lambda url, timeout: responses.pop(0))
    monkeypatch.setattr("lotr_sdk.client.time.sleep", lambda s: sleeps.append(s))

    client.movies.list()

    assert sleeps == [1.5]


def test_retries_on_connection_error_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    client = LOTRClient("token", base_url="https://example.test/v2", max_retries=2)

    sleeps: List[float] = []
    state = {"calls": 0}

    def fake_get(url: str, timeout: int) -> requests.Response:
        state["calls"] += 1
        if state["calls"] == 1:
            raise requests.ConnectionError("temporary")
        return _response(200)

    monkeypatch.setattr(client.session, "get", fake_get)
    monkeypatch.setattr("lotr_sdk.client.time.sleep", lambda s: sleeps.append(s))
    monkeypatch.setattr("lotr_sdk.client.random.uniform", lambda a, b: 0.0)

    payload = client.movies.list()

    assert payload["docs"] == []
    assert state["calls"] == 2
    assert len(sleeps) == 1


def test_raises_after_exhausting_network_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    client = LOTRClient("token", base_url="https://example.test/v2", max_retries=1)

    monkeypatch.setattr(
        client.session,
        "get",
        lambda url, timeout: (_ for _ in ()).throw(requests.Timeout("timeout")),
    )
    monkeypatch.setattr("lotr_sdk.client.time.sleep", lambda s: None)
    monkeypatch.setattr("lotr_sdk.client.random.uniform", lambda a, b: 0.0)

    with pytest.raises(APIRequestError):
        client.movies.list()


def test_does_not_retry_on_auth_error(monkeypatch: pytest.MonkeyPatch) -> None:
    client = LOTRClient("token", base_url="https://example.test/v2", max_retries=5)

    state = {"calls": 0}

    def fake_get(url: str, timeout: int) -> requests.Response:
        state["calls"] += 1
        return _response(401, {"message": "Unauthorized"})

    monkeypatch.setattr(client.session, "get", fake_get)

    with pytest.raises(AuthenticationError):
        client.movies.list()

    assert state["calls"] == 1
