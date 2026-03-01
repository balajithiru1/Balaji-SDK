# Poorn SDK

Production-oriented Python SDK for [The One API](https://the-one-api.dev/) focused on movie and quote endpoints.

Implemented endpoints:
- `/movie`
- `/movie/{id}`
- `/movie/{id}/quote`
- `/quote`
- `/quote/{id}`

## Why this structure
- Resource-oriented design (`movies`, `quotes`) keeps endpoint logic grouped and extensible.
- Central HTTP client handles auth, transport, and error normalization once.
- Filter builder supports The One API operator syntax while keeping call-sites readable.
- Tests validate URL/query/header behavior without requiring live network access.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

For development/test dependencies:

```bash
pip install -e .[dev]
```

## Quick start

```python
import os
from lotr_sdk import LOTRClient, fields

client = LOTRClient(api_key=os.environ["LOTR_API_KEY"])

movies = client.movies.list(limit=3)
print(movies["docs"])

movie_id = movies["docs"][0]["_id"]
movie_detail = client.movies.get(movie_id)
print(movie_detail["docs"][0]["name"])

quotes = client.movies.quotes(
    movie_id,
    limit=5,
    filters=[fields.dialog.regex("Ring")],
)
print(len(quotes["docs"]))
```

## Resiliency (Retry + Jitter)

The client includes adaptive retry for transient failures:
- Retries on network errors (`Timeout`, `ConnectionError`)
- Retries on transient HTTP statuses: `408, 425, 429, 500, 502, 503, 504`
- Uses `Retry-After` header when returned by API (for example on `429`)
- Otherwise uses exponential backoff with jitter

Configuration options on `LOTRClient(...)`:
- `max_retries` (default `3`)
- `backoff_base_seconds` (default `0.5`)
- `max_backoff_seconds` (default `8.0`)
- `jitter_ratio` (default `0.2`)

## Observability Hooks

You can pass `event_hook` to receive request lifecycle events.

```python
from pprint import pformat
from lotr_sdk import LOTRClient

def log_event(event: dict) -> None:
    print(pformat(event))

client = LOTRClient(api_key="token", event_hook=log_event)
client.movies.list(limit=1)
```

Event types:
- `request_attempt`
- `request_retry`
- `request_exception`
- `request_complete`

Common event fields include `path`, `url`, `attempt`, `status_code`, `elapsed_ms`, and `request_id` (if sent by API).

## Filtering

Two options are supported.

1. Fluent filter expressions (recommended):

```python
from lotr_sdk import fields

client.quotes.list(
    filters=[
        fields.character.eq("5cd99d4bde30eff6ebccfc15"),
        fields.dialog.regex("ring"),
    ]
)
```

2. Raw dictionary filters:

```python
client.movies.list(filters={"runtimeInMinutes>": 120, "name": "The Two Towers"})
```

Supported operations in fluent API:
- `eq`, `ne`
- `include`, `exclude`
- `lt`, `lte`, `gt`, `gte`
- `regex`
- `exists`

## API surface

```python
client.movies.list(limit=None, page=None, offset=None, sort=None, filters=None)
client.movies.get(movie_id)
client.movies.quotes(movie_id, limit=None, page=None, offset=None, sort=None, filters=None)

client.quotes.list(limit=None, page=None, offset=None, sort=None, filters=None)
client.quotes.get(quote_id)
```

## Errors

- `AuthenticationError` for 401/403
- `APIRequestError` for other 4xx/5xx failures

## Run tests

```bash
pytest
```

## Run demo locally

Set your token and run:

```bash
export LOTR_API_KEY="your-token"
PYTHONPATH=src python demo/demo.py
```

If you run without network access, demo requests will fail but this does not affect test execution.

## Examples

Run from project root:

```bash
export LOTR_API_KEY="your-token"
PYTHONPATH=src python examples/basic_usage.py
PYTHONPATH=src python examples/filtering_examples.py
PYTHONPATH=src python examples/observability_retry_demo.py
```
