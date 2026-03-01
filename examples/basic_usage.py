"""Basic SDK usage for movie and quote endpoints."""

from __future__ import annotations

import os

from lotr_sdk import LOTRClient


def main() -> int:
    api_key = os.getenv("LOTR_API_KEY")
    if not api_key:
        print("Set LOTR_API_KEY first")
        return 1

    client = LOTRClient(api_key=api_key)

    movies = client.movies.list(limit=2)
    print(f"Movies fetched: {len(movies['docs'])}")

    if movies["docs"]:
        movie_id = movies["docs"][0]["_id"]
        movie = client.movies.get(movie_id)
        print("Movie name:", movie["docs"][0].get("name"))

    quotes = client.quotes.list(limit=2)
    print(f"Quotes fetched: {len(quotes['docs'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
