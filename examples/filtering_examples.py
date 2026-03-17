"""Filtering examples using fluent and raw syntax."""

from __future__ import annotations

import os

from lotr_sdk import LOTRClient, fields
from lotr_sdk.exceptions import APIRequestError


def main() -> int:
    api_key = os.getenv("LOTR_API_KEY")
    if not api_key:
        print("Set LOTR_API_KEY first")
        return 1

    client = LOTRClient(api_key=api_key)

    fluent = client.quotes.list(
        limit=5,
        filters=[
            fields.dialog.regex("ring"),
            fields.character.ne("5cd99d4bde30eff6ebccfea0"),
        ],
    )
    print(f"Fluent filter quotes: {len(fluent['docs'])}")

    try:
        first_movie = client.movies.list(limit=1)
        movie_name = first_movie["docs"][0].get("name", "The Lord of the Rings Series")
        raw = client.movies.list(filters={"name": movie_name})
        print(f"Raw filter movies: {len(raw['docs'])}")
    except (APIRequestError, IndexError, KeyError):
        print("Raw filter failed; skipping.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
