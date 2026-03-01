"""Retry + observability hook demonstration."""

from __future__ import annotations

import os
from pprint import pformat

from lotr_sdk import LOTRClient


def print_event(event: dict) -> None:
    print("EVENT:", pformat(event))


def main() -> int:
    api_key = os.getenv("LOTR_API_KEY")
    if not api_key:
        print("Set LOTR_API_KEY first")
        return 1

    client = LOTRClient(
        api_key=api_key,
        max_retries=3,
        backoff_base_seconds=0.5,
        max_backoff_seconds=5.0,
        jitter_ratio=0.25,
        event_hook=print_event,
    )

    result = client.movies.list(limit=1)
    print("Fetched docs:", len(result["docs"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
