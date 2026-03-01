# SDK Design

## Goals
- Implement the required movie and quote endpoints.
- Keep architecture extensible for future endpoints.
- Provide ergonomic filtering aligned with The One API query syntax.
- Be production-ready in fundamentals (errors, testability, clear boundaries).

## High-level architecture

- `LOTRClient` (`src/lotr_sdk/client.py`)
  - Owns base URL, auth header, timeout, shared HTTP session.
  - Handles response parsing and error mapping.
- `MovieResource` / `QuoteResource` (`src/lotr_sdk/resources.py`)
  - Encapsulate endpoint-specific path and query construction.
- `filters.py`
  - Encodes API-specific filter operators through fluent helpers.
- `exceptions.py`
  - Strongly typed SDK exceptions for consumers.

This split keeps transport concerns separated from endpoint concerns and avoids duplicated request/response logic.

## Endpoint mapping

- `movies.list()` -> `GET /movie`
- `movies.get(movie_id)` -> `GET /movie/{id}`
- `movies.quotes(movie_id)` -> `GET /movie/{id}/quote`
- `quotes.list()` -> `GET /quote`
- `quotes.get(quote_id)` -> `GET /quote/{id}`

## Filtering approach

The One API uses operator-based query syntax (`name=`, `name!=`, `runtimeInMinutes>`, regex, existence checks).

Two input styles are accepted:
1. `FilterExpr` list through fluent helper `fields.<field>.<op>(value)`.
2. Raw dictionary for direct control.

This balances beginner usability and power-user flexibility.

## Error handling

- 401/403 => `AuthenticationError`
- Other non-2xx => `APIRequestError(status_code=...)`
- Unexpected success payload shape => `APIRequestError`

A stable error model lets SDK users implement retry/logging flows cleanly.

## Resiliency strategy

- Retries transient failures in `LOTRClient` for idempotent GET requests.
- Retry triggers:
  - Network-level `requests.Timeout` and `requests.ConnectionError`
  - HTTP: `408, 425, 429, 500, 502, 503, 504`
- Delay strategy:
  - Prefer server-provided `Retry-After` when available.
  - Otherwise exponential backoff with bounded jitter.
- Tunable via constructor args (`max_retries`, `backoff_base_seconds`, `max_backoff_seconds`, `jitter_ratio`).
- Explicitly does not retry authentication failures (`401`, `403`) to avoid useless repeated calls.

## Observability strategy

- `LOTRClient` accepts an optional `event_hook(event: dict)`.
- Hook is invoked on key request lifecycle stages:
  - `request_attempt`
  - `request_retry`
  - `request_exception`
  - `request_complete`
- Event payload includes diagnostics such as path, URL, attempt count, status code, elapsed time, retry delay, and request ID (if provided).
- Hook failures are swallowed so telemetry cannot break API calls.

## Testing strategy

- Unit tests use `requests-mock` to validate:
  - URL path construction
  - query and filter serialization
  - auth header inclusion
  - exception behavior
- Retry and observability tests use monkeypatched request/session behavior to validate deterministic retry timing and event emissions.
- No live HTTP dependency in CI/local tests.

## Extensibility notes

To add a new endpoint group later:
1. Create a new resource class.
2. Inject it from `LOTRClient.__init__`.
3. Reuse `_merge_params` and shared `client.get`.
4. Add resource-focused tests.

This minimizes blast radius for future features.
