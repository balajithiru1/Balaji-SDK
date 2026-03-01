"""Filtering examples using fluent and raw syntax."""

from __future__ import annotations

import os

from lotr_sdk import LOTRClient, fields


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

    raw = client.movies.list(filters={"runtimeInMinutes>": 120, "sort": "-runtimeInMinutes"})
    print(f"Raw filter movies: {len(raw['docs'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
