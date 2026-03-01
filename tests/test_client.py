from __future__ import annotations

from urllib.parse import unquote

import pytest

from lotr_sdk import LOTRClient
from lotr_sdk.exceptions import APIRequestError, AuthenticationError
from lotr_sdk.filters import fields


@pytest.fixture
def client() -> LOTRClient:
    return LOTRClient("test-token", base_url="https://example.test/v2")


def test_movie_list_endpoint_and_query(requests_mock, client: LOTRClient) -> None:
    requests_mock.get(
        "https://example.test/v2/movie",
        json={"docs": [], "total": 0, "limit": 10, "offset": 0, "page": 1, "pages": 1},
    )

    client.movies.list(limit=10, page=1)

    req = requests_mock.last_request
    assert req is not None
    assert req.qs["limit"] == ["10"]
    assert req.qs["page"] == ["1"]
    assert req.headers["Authorization"] == "Bearer test-token"


def test_movie_get_by_id(requests_mock, client: LOTRClient) -> None:
    movie_id = "5cd95395de30eff6ebccde5c"
    requests_mock.get(
        f"https://example.test/v2/movie/{movie_id}",
        json={"docs": [{"_id": movie_id}], "total": 1, "limit": 1, "offset": 0, "page": 1, "pages": 1},
    )

    payload = client.movies.get(movie_id)

    assert payload["docs"][0]["_id"] == movie_id


def test_movie_quote_endpoint_with_filter_objects(requests_mock, client: LOTRClient) -> None:
    movie_id = "5cd95395de30eff6ebccde5b"
    requests_mock.get(
        f"https://example.test/v2/movie/{movie_id}/quote",
        json={"docs": [], "total": 0, "limit": 5, "offset": 0, "page": 1, "pages": 1},
    )

    client.movies.quotes(movie_id, limit=5, filters=[fields.character.eq("abc"), fields.dialog.regex("Ring")])

    req = requests_mock.last_request
    assert req is not None
    decoded_query = unquote(req.query).lower()
    assert "limit=5" in decoded_query
    assert "character=abc" in decoded_query
    assert "dialog=/ring/" in decoded_query


def test_quote_list_with_dict_filters(requests_mock, client: LOTRClient) -> None:
    requests_mock.get(
        "https://example.test/v2/quote",
        json={"docs": [], "total": 0, "limit": 5, "offset": 0, "page": 1, "pages": 1},
    )

    client.quotes.list(sort="-dialog", filters={"character": "123", "runtimeInMinutes>": 100})

    req = requests_mock.last_request
    assert req is not None
    decoded_query = unquote(req.query).lower()
    assert "sort=-dialog" in decoded_query
    assert "character=123" in decoded_query
    assert "runtimeinminutes>100" in decoded_query


def test_quote_get_by_id(requests_mock, client: LOTRClient) -> None:
    quote_id = "5cd96e05de30eff6ebcce7e9"
    requests_mock.get(
        f"https://example.test/v2/quote/{quote_id}",
        json={"docs": [{"_id": quote_id}], "total": 1, "limit": 1, "offset": 0, "page": 1, "pages": 1},
    )

    payload = client.quotes.get(quote_id)

    assert payload["docs"][0]["_id"] == quote_id


def test_raises_auth_error(requests_mock, client: LOTRClient) -> None:
    requests_mock.get("https://example.test/v2/movie", status_code=401, json={"message": "Unauthorized"})

    with pytest.raises(AuthenticationError):
        client.movies.list()


def test_raises_api_error(requests_mock, client: LOTRClient) -> None:
    requests_mock.get("https://example.test/v2/movie", status_code=500, json={"message": "Server error"})

    with pytest.raises(APIRequestError) as exc:
        client.movies.list()

    assert exc.value.status_code == 500


def test_requires_api_key() -> None:
    with pytest.raises(ValueError):
        LOTRClient("")
