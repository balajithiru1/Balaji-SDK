

"""Manual demo runner for local validation against The One API."""

from __future__ import annotations

import os
import sys

from lotr_sdk import LOTRClient, fields


def main() -> int:
    api_key = os.getenv("LOTR_API_KEY")
    if not api_key:
        print("Please set LOTR_API_KEY environment variable.")
        return 1

    client = LOTRClient(api_key=api_key)

    movies = client.movies.list(limit=2)
    print(f"Fetched {len(movies['docs'])} movies")

    if not movies["docs"]:
        print("No movies returned")
        return 0

    movie_id = movies["docs"][0]["_id"]
    movie = client.movies.get(movie_id)
    print("First movie:", movie["docs"][0].get("name"))

    quotes = client.movies.quotes(movie_id, limit=3, filters=[fields.dialog.regex("Ring")])
    print(f"Fetched {len(quotes['docs'])} movie quotes matching regex")

    all_quotes = client.quotes.list(limit=3)
    print(f"Fetched {len(all_quotes['docs'])} general quotes")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
